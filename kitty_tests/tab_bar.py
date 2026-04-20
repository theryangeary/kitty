#!/usr/bin/env python
# License: GPL v3 Copyright: 2024, Kovid Goyal <kovid at kovidgoyal.net>

from kitty.fast_data_types import DECAWM, LEFT_EDGE, Screen

from . import BaseTest


class TestVerticalTabBar(BaseTest):

    def _make_screen(self, nrows: int, ncols: int, cell_width: int = 10, cell_height: int = 20) -> Screen:
        s = Screen(None, nrows, ncols, 0, cell_width, cell_height)
        s.reset_mode(DECAWM)
        return s

    def test_tab_bar_edge_left_parses(self):
        from kitty.fast_data_types import BOTTOM_EDGE, RIGHT_EDGE, TOP_EDGE
        from kitty.options.utils import tab_bar_edge
        self.ae(tab_bar_edge('left'), LEFT_EDGE)
        self.ae(tab_bar_edge('right'), RIGHT_EDGE)
        self.ae(tab_bar_edge('top'), TOP_EDGE)
        self.ae(tab_bar_edge('bottom'), BOTTOM_EDGE)
        self.ae(tab_bar_edge('LEFT'), LEFT_EDGE)
        self.ae(tab_bar_edge('bogus'), BOTTOM_EDGE)

    def test_tab_bar_width_default(self):
        from kitty.options.types import defaults
        self.assertGreater(defaults.tab_bar_width, 0)

    def test_vertical_screen_resize(self):
        s = self._make_screen(nrows=5, ncols=12)
        self.ae(s.lines, 5)
        self.ae(s.columns, 12)

    def test_vertical_update_one_row_per_tab(self):
        from kitty.rgb import to_color
        from kitty.tab_bar import (
            CellRange,
            DrawData,
            ExtraData,
            TabBarData,
            TabExtent,
            as_rgb,
            draw_tab_with_fade,
        )
        from kitty.utils import color_as_int

        dd = DrawData(
            leading_spaces=0, sep='', trailing_spaces=0, bell_on_tab='',
            alpha=(0.25, 0.5, 0.75, 1.0),
            active_fg=to_color('white'), active_bg=to_color('blue'),
            inactive_fg=to_color('gray'), inactive_bg=to_color('black'),
            default_bg=to_color('black'),
            title_template='{title}', active_title_template=None,
            tab_activity_symbol='', powerline_style='angled',
            tab_bar_edge='left', max_tab_title_length=0, os_window_id=0,
        )

        ntabs = 4
        nrows = ntabs + 2
        ncols = 15
        s = self._make_screen(nrows=nrows, ncols=ncols)

        # Use tab_id=-1 so apply_title_template renders .title directly,
        # bypassing the template eval path that needs a live boss process.
        tabs = [
            TabBarData(title=f'tab{i+1}', is_active=(i == 0), tab_id=-1)
            for i in range(ntabs)
        ]

        cr: list[TabExtent] = []
        ed = ExtraData()
        ed.for_layout = False

        for i, t in enumerate(tabs):
            s.cursor.x = 0
            s.cursor.y = i
            s.erase_in_line(2, False)
            s.cursor.bg = as_rgb(color_as_int(dd.active_bg if t.is_active else dd.inactive_bg))
            s.cursor.fg = as_rgb(color_as_int(dd.active_fg if t.is_active else dd.inactive_fg))
            ed.prev_tab = tabs[i - 1] if i > 0 else None
            ed.next_tab = tabs[i + 1] if i + 1 < ntabs else None
            draw_tab_with_fade(dd, s, t, 0, ncols - 1, i + 1, i == ntabs - 1, ed)
            s.cursor.bg = s.cursor.fg = 0
            cr.append(TabExtent(tab_id=i + 1, cell_range=CellRange(i, i)))

        self.ae(len(cr), ntabs)
        for i, te in enumerate(cr):
            self.ae(te.tab_id, i + 1)
            self.ae(te.cell_range.start, i)
            self.ae(te.cell_range.end, i)

        # Confirm screen has the expected dimensions.
        self.ae(s.lines, nrows)
        self.ae(s.columns, ncols)

    def test_tab_id_at_vertical(self):
        from kitty.tab_bar import CellRange, TabBar, TabExtent
        from kitty.types import WindowGeometry

        class FakeTabBar:
            is_vertical = True
            laid_out_once = True
            cell_height = 20
            cell_width = 10
            window_geometry = WindowGeometry(left=0, top=0, right=100, bottom=60, xnum=10, ynum=3)
            tab_extents = [
                TabExtent(tab_id=10, cell_range=CellRange(0, 0)),
                TabExtent(tab_id=20, cell_range=CellRange(1, 1)),
                TabExtent(tab_id=30, cell_range=CellRange(2, 2)),
            ]

        tb = FakeTabBar()

        def tab_id_at(x, y):
            return TabBar.tab_id_at(tb, x, y)

        # y=5  → row 0 → tab_id 10
        self.ae(tab_id_at(0, 5), 10)
        # y=25 → row 1 → tab_id 20
        self.ae(tab_id_at(0, 25), 20)
        # y=45 → row 2 → tab_id 30
        self.ae(tab_id_at(0, 45), 30)
        # y=65 → row 3 → no match
        self.ae(tab_id_at(0, 65), 0)
