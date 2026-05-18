"""
Navigation Handler module for BRT Shipping Management Application
Manages navigation between records and skip mode
"""

import pandas as pd
from typing import Optional, Tuple, Callable
from PyQt5.QtWidgets import QMessageBox, QWidget

from core.constants import CSVColumns, Messages


class NavigationHandler:
    """Handles navigation between shipment records"""

    def __init__(self, parent: QWidget):
        """Initialize navigation handler.

        Args:
            parent: Parent widget for dialogs
        """
        self.parent = parent
        self.skip_navigation_mode: bool = False

    def save_record_data(
        self,
        df_spedizioni: pd.DataFrame,
        current_index: int,
        colli: int,
        peso: float,
        volume: float
    ) -> None:
        """Save colli, peso and volume data to current record.

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index
            colli: Number of packages
            peso: Weight in kg
            volume: Volume in m³
        """
        df_spedizioni.loc[df_spedizioni.index[current_index], 'VABNCL'] = str(colli)
        df_spedizioni.loc[df_spedizioni.index[current_index], 'VABPKB'] = f"{peso:.1f}"
        df_spedizioni.loc[df_spedizioni.index[current_index], 'VABVLB'] = f"{volume:.4f}"

    def skip_current_record(
        self,
        df_spedizioni: pd.DataFrame,
        current_index: int
    ) -> None:
        """Mark current record as skipped.

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index
        """
        df_spedizioni.loc[df_spedizioni.index[current_index], 'VABNCL'] = 'SKIP'
        df_spedizioni.loc[df_spedizioni.index[current_index], 'VABPKB'] = 'SKIP'
        df_spedizioni.loc[df_spedizioni.index[current_index], 'VABVLB'] = 'SKIP'

    def go_to_previous(
        self,
        df_spedizioni: Optional[pd.DataFrame],
        current_index: int
    ) -> Optional[int]:
        """Navigate to previous record.

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index

        Returns:
            Optional[int]: New index or None if cannot go back
        """
        if df_spedizioni is None or current_index == 0:
            return None

        # Exit skip navigation mode
        self.skip_navigation_mode = False

        return current_index - 1

    def go_to_next(
        self,
        df_spedizioni: pd.DataFrame,
        current_index: int
    ) -> Optional[int]:
        """Navigate to next record.

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index

        Returns:
            Optional[int]: New index or None if already at last
        """
        total = len(df_spedizioni)
        if current_index >= total - 1:
            return None

        return current_index + 1

    def go_to_next_with_skip(
        self,
        df_spedizioni: pd.DataFrame,
        current_index: int
    ) -> int:
        """Navigate to next record (stays at last if already there).

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index

        Returns:
            int: New index (same if at last)
        """
        total = len(df_spedizioni)
        if current_index < total - 1:
            return current_index + 1
        return current_index

    def find_next_skipped(
        self,
        df_spedizioni: pd.DataFrame,
        current_index: int
    ) -> Optional[int]:
        """Find next skipped record index.

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index

        Returns:
            Optional[int]: Index of next skipped record or None if none found
        """
        # Find all skipped records
        skipped_indices = df_spedizioni[df_spedizioni['VABNCL'] == 'SKIP'].index.tolist()

        if not skipped_indices:
            return None

        # Look for first skipped record AFTER current index
        for idx in skipped_indices:
            idx_pos = df_spedizioni.index.get_loc(idx)
            # Ensure we have an int (get_loc can return int, slice, or ndarray)
            if isinstance(idx_pos, int) and idx_pos > current_index:
                return idx_pos

        # If there are none after, take the first one (restart from beginning)
        first_pos = df_spedizioni.index.get_loc(skipped_indices[0])
        return first_pos if isinstance(first_pos, int) else None

    def goto_next_skipped(
        self,
        df_spedizioni: Optional[pd.DataFrame],
        current_index: int
    ) -> Optional[int]:
        """Go to next skipped record (SKIP).

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index

        Returns:
            Optional[int]: New index or None if no skipped records
        """
        if df_spedizioni is None:
            return None

        next_skipped = self.find_next_skipped(df_spedizioni, current_index)

        if next_skipped is None:
            QMessageBox.information(self.parent, Messages.TITLE_INFO, Messages.MSG_NO_SKIPPED)
            self.skip_navigation_mode = False
            return None

        # Activate skip navigation mode
        self.skip_navigation_mode = True

        return next_skipped

    def handle_save_and_next_unified(
        self,
        df_spedizioni: pd.DataFrame,
        current_index: int
    ) -> int:
        """Handle navigation after save in unified mode (skip mode aware).

        Args:
            df_spedizioni: DataFrame with shipment data
            current_index: Current record index

        Returns:
            int: New index after navigation
        """
        # If in skip navigation mode, go to next skipped
        if self.skip_navigation_mode:
            next_skipped = self.find_next_skipped(df_spedizioni, current_index)

            if next_skipped is None:
                # No more skipped records! Exit mode and find first empty record (if exists)
                self.skip_navigation_mode = False

                # Look for first NOT completed record
                empty_indices = df_spedizioni[df_spedizioni['VABNCL'] == ''].index.tolist()

                if empty_indices:
                    # There are still empty records to fill - go to first empty record
                    first_empty_pos = df_spedizioni.index.get_loc(empty_indices[0])
                    # Ensure we have an int (get_loc can return int, slice, or ndarray)
                    if isinstance(first_empty_pos, int):
                        return first_empty_pos
                    else:
                        # Fallback to last record if we can't get a valid position
                        return len(df_spedizioni) - 1
                else:
                    # All completed! Go to last record
                    return len(df_spedizioni) - 1

            return next_skipped
        else:
            # Normal mode: go to next in sequence
            total = len(df_spedizioni)
            is_last = current_index >= total - 1

            if not is_last:
                return current_index + 1

            return current_index
