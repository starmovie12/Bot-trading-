"""Recorder: market data ka append-only journal (hash-chain ke saath) aur usse backtest ke liye candles/option book.

Raasta: live feed (M2) -> JournalWriter -> din ki file -> read_journal -> candles_from_ticks / RecordedBook -> backtest.
"""
