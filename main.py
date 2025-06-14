# Standard library imports
import sys
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Union, Tuple
from calendar import monthrange
from dateutil.relativedelta import relativedelta

# Third-party imports
import pandas as pd
import numpy as np

# Local imports
import tick_db as db
import rsi_sample as dw

# === Constants ===
# Date and Time Constants
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_START_DATE = '2017-01-01 00:00:00'
INITIAL_DATE = '2017-01-01 00:00:00'

# Trading Constants
DEFAULT_WINDOW_SIZE = 20
ELLIOTT_WAVE_PATTERN_LENGTH = 5
EXPECTED_WAVE_PATTERN = ['up', 'down', 'up', 'down', 'up']

# Financial Constants
DEFAULT_INITIAL_BALANCE = Decimal('10000000')  # 10,000,000 KRW
DEFAULT_MIN_TRADE_PRICE = Decimal('500')  # 최소 거래 금액
TRADING_FEE_RATE = Decimal('0.0005')  # 0.05% 거래 수수료

# Technical Analysis Constants
RSI_PERIODS = {
    'OVERSOLD': 30,
    'OVERBOUGHT': 70,
    'NEUTRAL': 50
}

PRICE_CHANGE_RATES = {
    'MIN': Decimal('1.01'),
    'MAX': Decimal('1.01')
}

# Fibonacci Ratios
FIBONACCI_LEVELS = {
    'LEVEL_236': Decimal('0.236'),
    'LEVEL_382': Decimal('0.382'),
    'LEVEL_500': Decimal('0.500'),
    'LEVEL_618': Decimal('0.618'),
    'LEVEL_786': Decimal('0.786')
}

# Display Configuration
CHART_CONFIG = {
    'DISPLAY_ENABLED': False,
    'FIGURE_SIZE': (15, 8),
    'DPI': 100
}

# Logging Configuration
LOG_CONFIG = {
    'FORMAT': '%(message)s',
    # 'LEVEL': logging.INFO
    'LEVEL': logging.DEBUG
}

# 설정
TRADING_CONFIG = {
    'time_intervals': ['60'],  # 분 단위
    # 'tickers': ['KRW-XRP', 'KRW-ETH'],
    'tickers': ['KRW-ETH'],
    'test_periods': {
        # 2020: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # 전체 월 테스트
        # 2021: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # 전체 월 테스트
        # 2022: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # 전체 월 테스트
        # 2023: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # 전체 월 테스트
        2024: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # 전체 월 테스트
        # 2024: [1,2],  # 전체 월 테스트
        # 2018: [3, 6, 9, 12],  # 분기별 테스트
        # 2019: [6, 12],  # 반기별 테스트
        # 2020: [12]  # 연간 테스트
    }
}


# === Data Classes and Type Definitions ===
@dataclass
class TradingConfig:
    """거래 설정을 위한 데이터 클래스"""
    INITIAL_BALANCE: Decimal = DEFAULT_INITIAL_BALANCE
    MIN_PRICE_CHANGE_RATE: Decimal = PRICE_CHANGE_RATES['MIN']
    MAX_PRICE_CHANGE_RATE: Decimal = PRICE_CHANGE_RATES['MAX']
    RSI_OVERSOLD: int = RSI_PERIODS['OVERSOLD']
    RSI_OVERBOUGHT: int = RSI_PERIODS['OVERBOUGHT']
    DISPLAY_CHART: bool = CHART_CONFIG['DISPLAY_ENABLED']
    TRADING_FEE: Decimal = TRADING_FEE_RATE


@dataclass
class TradingState:
    """거래 상태를 추적하기 위한 데이터 클래스"""
    balance: Decimal
    coin_quantity: Decimal
    min_price: Decimal
    max_price: Decimal
    start_price: Decimal
    end_price: Decimal
    total_fee: Decimal = Decimal('0')
    trade_count: int = 0


@dataclass
class TradeInfo:
    """개별 거래 정보를 저장하기 위한 데이터 클래스"""
    timestamp: datetime
    type: str  # 'BUY' or 'SELL'
    price: Decimal
    quantity: Decimal
    total_amount: Decimal
    fee: Decimal


@dataclass
class PeriodResult:
    """기간별 결과를 저장하는 데이터 클래스"""
    trading_profit: float
    coin_change_rate: float
    start_price: float
    end_price: float


class TradingPeriod:
    def __init__(self, start: datetime, end: datetime, year: int, month: int):
        self.start = start
        self.end = end
        self.year = year
        self.month = month


class TradingResult:
    """거래 결과를 저장하고 관리하는 클래스"""

    def __init__(self):
        self.buy_orders: List[float] = []
        self.sell_orders: List[float] = []
        self.trades: List[TradeInfo] = []
        self.profit_history: List[Tuple[datetime, Decimal]] = []

    def add_trade(self, trade: TradeInfo) -> None:
        """거래 기록 추가"""
        self.trades.append(trade)

    def add_profit_point(self, timestamp: datetime, profit: Decimal) -> None:
        """수익률 포인트 추가"""
        self.profit_history.append((timestamp, profit))


# === Utility Functions ===
def setup_logging() -> None:
    """로깅 설정 초기화"""
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(LOG_CONFIG['FORMAT']))
    logger = logging.getLogger()
    logger.addHandler(ch)
    logger.setLevel(LOG_CONFIG['LEVEL'])


def calculate_trade_fee(amount: Decimal) -> Decimal:
    """거래 수수료 계산"""
    return amount * TRADING_FEE_RATE


def format_currency(amount: Decimal) -> str:
    """통화 형식으로 포맷팅"""
    return f"{amount:,.2f} KRW"


def format_percentage(value: Decimal) -> str:
    """백분율 형식으로 포맷팅"""
    return f"{value:,.2f}%"


def get_selected_periods(config: Dict) -> List[TradingPeriod]:
    """설정된 연도와 월에 대한 기간 생성"""
    periods = []
    test_periods = config.get('test_periods', {})

    for year, months in test_periods.items():
        for month in months:
            start_date = datetime(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day, 23, 59, 59)
            periods.append(TradingPeriod(start_date, end_date, year, month))

    return sorted(periods, key=lambda x: (x.year, x.month))


def format_month_name(month: int) -> str:
    """월 이름 포맷팅"""
    return {
        1: "1월", 2: "2월", 3: "3월", 4: "4월",
        5: "5월", 6: "6월", 7: "7월", 8: "8월",
        9: "9월", 10: "10월", 11: "11월", 12: "12월"
    }[month]


def print_trading_results(results: Dict) -> None:
    """거래 결과 출력 (코인 변동률 포함)"""
    logging.info("\n========== Trading Results ==========")

    total_overall_profit = 0
    total_overall_coin_change = 0
    total_periods = 0

    for ticker, yearly_data in results.items():
        logging.info(f"\n[{ticker}]")
        total_profit = 0
        total_coin_change = 0
        ticker_periods = 0

        for year, monthly_data in sorted(yearly_data.items()):
            year_profit = 0
            year_coin_change = 0
            year_periods = 0

            logging.info(f"\n{year}년:")
            for month, period_result in sorted(monthly_data.items()):
                if isinstance(period_result, PeriodResult):
                    trading_profit = period_result.trading_profit
                    coin_change = period_result.coin_change_rate
                    start_price = period_result.start_price
                    end_price = period_result.end_price
                else:
                    # 기존 형식 호환성을 위해
                    trading_profit = period_result
                    coin_change = 0
                    start_price = 0
                    end_price = 0

                year_profit += trading_profit
                year_coin_change += coin_change
                year_periods += 1

                month_name = format_month_name(month)
                profit_str = f"{trading_profit:+.2f}%".rjust(10)
                coin_change_str = f"{coin_change:+.2f}%".rjust(10)

                logging.info(f"  {month_name}: 거래수익 {profit_str} | 코인변동 {coin_change_str}")

                if start_price > 0 and end_price > 0:
                    logging.info(f"       시작가: {start_price:,.0f} -> 종료가: {end_price:,.0f}")

            # 연간 합계 출력
            avg_year_coin_change = year_coin_change / year_periods if year_periods > 0 else 0
            logging.info(f"  연간 합계: 거래수익 {year_profit:+.2f}% | 코인변동 평균 {avg_year_coin_change:+.2f}%")

            total_profit += year_profit
            total_coin_change += year_coin_change
            ticker_periods += year_periods

        # 코인별 총 수익률 출력
        avg_ticker_coin_change = total_coin_change / ticker_periods if ticker_periods > 0 else 0
        logging.info(f"\n{ticker} 총 거래수익률: {total_profit:+.2f}%")
        logging.info(f"{ticker} 평균 코인변동률: {avg_ticker_coin_change:+.2f}%")
        logging.info(f"{ticker} 거래 대비 코인 성과: {total_profit - avg_ticker_coin_change:+.2f}%p")

        total_overall_profit += total_profit
        total_overall_coin_change += total_coin_change
        total_periods += ticker_periods

    # 전체 통계
    avg_overall_coin_change = total_overall_coin_change / total_periods if total_periods > 0 else 0
    logging.info(f"\n전체 코인 총 거래수익률: {total_overall_profit:+.2f}%")
    logging.info(f"전체 코인 평균 변동률: {avg_overall_coin_change:+.2f}%")
    logging.info(f"전체 거래 대비 코인 성과: {total_overall_profit - avg_overall_coin_change:+.2f}%p")
    logging.info("\n==================================\n")


def initialize_results_structure(tickers: List[str], periods: List[TradingPeriod]) -> Dict:
    """결과 저장을 위한 중첩 딕셔너리 초기화"""
    results = {}
    for ticker in tickers:
        results[ticker] = {}
        for period in periods:
            if period.year not in results[ticker]:
                results[ticker][period.year] = {}
            results[ticker][period.year][period.month] = PeriodResult(0, 0, 0, 0)
    return results


# === Elliott Wave Analysis Functions ===
def check_elliott_buy_pattern(data: pd.DataFrame, index: int) -> tuple:
    """엘리어트 파동 매수 패턴 체크"""
    if index < ELLIOTT_WAVE_PATTERN_LENGTH:
        return False, "Not enough data for Elliott wave analysis"

    try:
        # 최근 5개 구간의 가격 변동 방향 분석
        wave_pattern = []
        for i in range(index - ELLIOTT_WAVE_PATTERN_LENGTH + 1, index + 1):
            if i == 0:
                continue

            current_price = data.iloc[i]['close']
            previous_price = data.iloc[i - 1]['close']

            if current_price > previous_price:
                wave_pattern.append('up')
            else:
                wave_pattern.append('down')

        # 엘리어트 파동 패턴 확인 (상승-하락-상승-하락-상승)
        if len(wave_pattern) >= 4:  # 최소 4개 패턴 필요
            is_elliott_pattern = (
                    wave_pattern == EXPECTED_WAVE_PATTERN[-len(wave_pattern):] or
                    wave_pattern == EXPECTED_WAVE_PATTERN[:len(wave_pattern)]
            )

            if is_elliott_pattern:
                return True, f"Elliott wave pattern detected: {wave_pattern}"

        return False, f"Pattern not matched: {wave_pattern}"

    except (IndexError, KeyError) as e:
        return False, f"Error in Elliott wave analysis: {str(e)}"


def check_elliott_sell_pattern(data: pd.DataFrame, index: int) -> tuple:
    """엘리어트 파동 매도 패턴 체크"""
    if index < ELLIOTT_WAVE_PATTERN_LENGTH:
        return False, "Not enough data for Elliott wave analysis"

    try:
        # 최근 5개 구간의 가격 변동 방향 분석
        wave_pattern = []
        for i in range(index - ELLIOTT_WAVE_PATTERN_LENGTH + 1, index + 1):
            if i == 0:
                continue

            current_price = data.iloc[i]['close']
            previous_price = data.iloc[i - 1]['close']

            if current_price > previous_price:
                wave_pattern.append('up')
            else:
                wave_pattern.append('down')

        # 매도 신호: 5파동 완성 후 하락 시작
        if len(wave_pattern) >= 5:
            # 완전한 5파동 패턴이 완성되었는지 확인
            is_complete_elliott = wave_pattern == EXPECTED_WAVE_PATTERN

            # 또는 상승 추세 후 하락 전환점 감지
            recent_trend_reversal = (
                    len(wave_pattern) >= 3 and
                    wave_pattern[-3:] == ['up', 'up', 'down']  # 연속 상승 후 하락
            )

            if is_complete_elliott:
                return True, f"Complete Elliott wave pattern for sell: {wave_pattern}"
            elif recent_trend_reversal:
                return True, f"Trend reversal detected for sell: {wave_pattern}"

        return False, f"Sell pattern not detected: {wave_pattern}"

    except (IndexError, KeyError) as e:
        return False, f"Error in Elliott sell pattern analysis: {str(e)}"


def analyze_wave_strength(data: pd.DataFrame, index: int, wave_length: int = 5) -> Dict:
    """파동 강도 분석"""
    if index < wave_length:
        return {'strength': 0, 'direction': 'neutral', 'volatility': 0}

    try:
        prices = []
        for i in range(index - wave_length + 1, index + 1):
            prices.append(data.iloc[i]['close'])

        # 변동성 계산
        price_changes = []
        for i in range(1, len(prices)):
            change_rate = abs(prices[i] - prices[i - 1]) / prices[i - 1] * 100
            price_changes.append(change_rate)

        avg_volatility = sum(price_changes) / len(price_changes) if price_changes else 0

        # 전체 방향성 계산
        total_change = (prices[-1] - prices[0]) / prices[0] * 100

        # 강도 계산 (변동성과 방향성 결합)
        strength = avg_volatility * (1 + abs(total_change) / 100)

        direction = 'up' if total_change > 0 else 'down' if total_change < 0 else 'neutral'

        return {
            'strength': strength,
            'direction': direction,
            'volatility': avg_volatility,
            'total_change_rate': total_change
        }

    except Exception as e:
        return {'strength': 0, 'direction': 'neutral', 'volatility': 0, 'error': str(e)}


def check_fibonacci_levels(data: pd.DataFrame, index: int, lookback_period: int = 20) -> Dict:
    """피보나치 되돌림 수준 확인"""
    if index < lookback_period:
        return {'at_fibonacci_level': False, 'level': None, 'support_resistance': None}

    try:
        # 최근 기간의 최고가/최저가 찾기
        prices = []
        for i in range(index - lookback_period + 1, index + 1):
            prices.append(data.iloc[i]['close'])

        high_price = max(prices)
        low_price = min(prices)
        current_price = data.iloc[index]['close']

        # 피보나치 되돌림 수준 계산
        price_range = high_price - low_price
        fibonacci_levels = {}

        for level_name, ratio in FIBONACCI_LEVELS.items():
            fib_price = high_price - (price_range * ratio)
            fibonacci_levels[level_name] = float(fib_price)

        # 현재 가격이 피보나치 수준 근처에 있는지 확인 (±1% 허용)
        tolerance = price_range * Decimal('0.01')  # 1% 허용 범위

        for level_name, fib_price in fibonacci_levels.items():
            if abs(current_price - fib_price) <= float(tolerance):
                # 지지/저항 수준 판단
                if current_price <= (high_price + low_price) / 2:
                    support_resistance = 'support'
                else:
                    support_resistance = 'resistance'

                return {
                    'at_fibonacci_level': True,
                    'level': level_name,
                    'fib_price': fib_price,
                    'current_price': float(current_price),
                    'support_resistance': support_resistance,
                    'all_levels': fibonacci_levels
                }

        return {
            'at_fibonacci_level': False,
            'level': None,
            'support_resistance': None,
            'all_levels': fibonacci_levels
        }

    except Exception as e:
        return {'at_fibonacci_level': False, 'level': None, 'error': str(e)}


def enhanced_elliott_analysis(data: pd.DataFrame, index: int) -> Dict:
    """향상된 엘리어트 파동 분석 (파동 강도 + 피보나치 결합)"""
    elliott_buy_result, elliott_buy_msg = check_elliott_buy_pattern(data, index)
    elliott_sell_result, elliott_sell_msg = check_elliott_sell_pattern(data, index)

    wave_analysis = analyze_wave_strength(data, index)
    fibonacci_analysis = check_fibonacci_levels(data, index)

    # 종합 신호 생성
    combined_signal = {
        'elliott_buy': elliott_buy_result,
        'elliott_sell': elliott_sell_result,
        'wave_strength': wave_analysis['strength'],
        'wave_direction': wave_analysis['direction'],
        'at_fibonacci': fibonacci_analysis['at_fibonacci_level'],
        'fibonacci_level': fibonacci_analysis.get('level'),
        'support_resistance': fibonacci_analysis.get('support_resistance')
    }

    # 매수/매도 신호 강도 계산
    buy_signal_strength = 0
    sell_signal_strength = 0

    if elliott_buy_result:
        buy_signal_strength += 30
    if elliott_sell_result:
        sell_signal_strength += 30

    # 파동 강도 반영
    if wave_analysis['direction'] == 'up' and wave_analysis['strength'] > 2:
        buy_signal_strength += 20
    elif wave_analysis['direction'] == 'down' and wave_analysis['strength'] > 2:
        sell_signal_strength += 20

    # 피보나치 수준 반영
    if fibonacci_analysis['at_fibonacci_level']:
        if fibonacci_analysis['support_resistance'] == 'support':
            buy_signal_strength += 15
        elif fibonacci_analysis['support_resistance'] == 'resistance':
            sell_signal_strength += 15

    combined_signal['buy_signal_strength'] = buy_signal_strength
    combined_signal['sell_signal_strength'] = sell_signal_strength
    combined_signal['elliott_buy_msg'] = elliott_buy_msg
    combined_signal['elliott_sell_msg'] = elliott_sell_msg

    return combined_signal


# === BackTest Class ===
class BackTest:
    def __init__(self, config: TradingConfig = None):
        self.config = config or TradingConfig()
        self.state = TradingState(
            balance=self.config.INITIAL_BALANCE,
            coin_quantity=Decimal('0'),
            min_price=Decimal('0'),
            max_price=Decimal('0'),
            start_price=Decimal('0'),
            end_price=Decimal('0')
        )
        self.result = TradingResult()
        setup_logging()

    def check_buy_condition(self, price: Decimal, data: Optional[pd.DataFrame] = None,
                            current_index: Optional[int] = None) -> bool:
        """매수 조건 확인 (엘리어트 파동 분석 포함)"""
        if self.state.min_price == 0:
            self.state.min_price = price
            return False

        should_buy = False

        # 기본 가격 조건
        if self.state.min_price * self.config.MIN_PRICE_CHANGE_RATE < price:
            self.state.min_price = price
            should_buy = True
        else:
            self.state.min_price = price

        # 엘리어트 파동 분석 추가
        if data is not None and current_index is not None:
            elliott_analysis = enhanced_elliott_analysis(data, current_index)

            # 강한 매수 신호 (50점 이상)
            if elliott_analysis['buy_signal_strength'] >= 50:
                should_buy = True
                logging.debug(f"Strong Elliott buy signal: {elliott_analysis['buy_signal_strength']}")

            # 중간 매수 신호 (30점 이상) - 기본 조건과 결합
            elif elliott_analysis['buy_signal_strength'] >= 30 and should_buy:
                logging.debug(f"Combined buy signal: {elliott_analysis['buy_signal_strength']}")

        return should_buy

    def check_sell_condition(self, price: Decimal, data: Optional[pd.DataFrame] = None,
                             current_index: Optional[int] = None) -> bool:
        """매도 조건 확인 (엘리어트 파동 분석 포함)"""
        if self.state.max_price == 0:
            self.state.max_price = price
            return False

        should_sell = False

        # 기본 가격 조건
        if self.state.max_price * self.config.MAX_PRICE_CHANGE_RATE > price:
            self.state.max_price = price
            should_sell = True
        else:
            self.state.max_price = price

        # 엘리어트 파동 분석 추가
        if data is not None and current_index is not None:
            elliott_analysis = enhanced_elliott_analysis(data, current_index)

            # 강한 매도 신호 (50점 이상)
            if elliott_analysis['sell_signal_strength'] >= 50:
                should_sell = True
                logging.debug(f"Strong Elliott sell signal: {elliott_analysis['sell_signal_strength']}")

            # 중간 매도 신호 (30점 이상) - 기본 조건과 결합
            elif elliott_analysis['sell_signal_strength'] >= 30 and should_sell:
                logging.debug(f"Combined sell signal: {elliott_analysis['sell_signal_strength']}")

        return should_sell

    def execute_buy(self, price: Decimal, timestamp: datetime = None,
                    force: bool = False, data: Optional[pd.DataFrame] = None,
                    current_index: Optional[int] = None) -> None:
        """매수 실행"""
        if timestamp is None:
            timestamp = datetime.now()

        if self.state.balance > price:
            should_buy = force or self.check_buy_condition(price, data, current_index)

            if should_buy:
                buy_quantity = Decimal(str(int(self.state.balance / price)))
                total_amount = price * buy_quantity
                fee = calculate_trade_fee(total_amount)

                if self.state.balance >= (total_amount + fee):
                    self.state.coin_quantity += buy_quantity
                    self.state.balance -= (total_amount + fee)
                    self.state.total_fee += fee
                    self.state.trade_count += 1

                    trade_info = TradeInfo(
                        timestamp=timestamp,
                        type='BUY',
                        price=price,
                        quantity=buy_quantity,
                        total_amount=total_amount,
                        fee=fee
                    )

                    self.result.add_trade(trade_info)
                    self.result.buy_orders.append(float(price))
                    self.result.sell_orders.append(-1)

                    logging.debug(
                        f"[매수] 가격: {format_currency(price)}, "
                        f"수량: {buy_quantity}, "
                        f"총액: {format_currency(total_amount)}, "
                        f"수수료: {format_currency(fee)}"
                    )
                    logging.debug(f"[잔고] {format_currency(self.state.balance)}")
            else:
                self._append_no_trade()
        else:
            self._append_no_trade()

    def execute_sell(self, price: Decimal, timestamp: datetime = None,
                     force: bool = False, data: Optional[pd.DataFrame] = None,
                     current_index: Optional[int] = None) -> None:
        """매도 실행"""
        if timestamp is None:
            timestamp = datetime.now()

        if self.state.coin_quantity > 0:
            should_sell = force or self.check_sell_condition(price, data, current_index)

            if should_sell:
                total_amount = price * self.state.coin_quantity
                fee = calculate_trade_fee(total_amount)

                self.state.balance += (total_amount - fee)
                self.state.total_fee += fee
                self.state.trade_count += 1

                trade_info = TradeInfo(
                    timestamp=timestamp,
                    type='SELL',
                    price=price,
                    quantity=self.state.coin_quantity,
                    total_amount=total_amount,
                    fee=fee
                )

                self.result.add_trade(trade_info)
                self.result.sell_orders.append(float(price))
                self.result.buy_orders.append(-1)

                logging.debug(
                    f"[매도] 가격: {format_currency(price)}, "
                    f"수량: {self.state.coin_quantity}, "
                    f"총액: {format_currency(total_amount)}, "
                    f"수수료: {format_currency(fee)}"
                )
                logging.debug(f"[잔고] {format_currency(self.state.balance)}")

                self.state.coin_quantity = Decimal('0')
            else:
                self._append_no_trade()
        else:
            self._append_no_trade()

    def _append_no_trade(self) -> None:
        """미체결 주문 기록"""
        self.result.buy_orders.append(-1)
        self.result.sell_orders.append(-1)

    def display_account_summary(self, ticker: str, interval: str,
                                start_time: datetime, end_time: datetime) -> Tuple[float, float]:
        """계좌 요약 정보 표시 및 수익률과 코인 변동률 반환"""
        total_profit = self.state.balance - self.config.INITIAL_BALANCE
        profit_rate = (total_profit * Decimal('100') / self.config.INITIAL_BALANCE)

        if self.state.start_price > 0:
            coin_change_rate = ((self.state.end_price - self.state.start_price) *
                                Decimal('100') / self.state.start_price)
        else:
            coin_change_rate = Decimal('0')

        logging.info("\n" + "=" * 70)
        logging.info(f"종목, 주기: {ticker}, {interval}")
        logging.info(f"기간: {start_time} ~ {end_time}")
        logging.info("-" * 70)
        logging.info(f"초기자본: {format_currency(self.config.INITIAL_BALANCE)}")
        logging.info(f"최종자본: {format_currency(self.state.balance)}")
        logging.info(f"순손익: {format_currency(total_profit)}")
        logging.info(f"거래횟수: {self.state.trade_count}회")
        logging.info(f"총 수수료: {format_currency(self.state.total_fee)}")
        logging.info("-" * 70)
        logging.info(f"시작가격: {format_currency(self.state.start_price)}")
        logging.info(f"종료가격: {format_currency(self.state.end_price)}")
        logging.info(f"코인가격 변동률: {format_percentage(coin_change_rate)}")
        logging.info(f"거래 수익률: {format_percentage(profit_rate)}")
        logging.info(f"거래 vs 코인 성과: {format_percentage(profit_rate - coin_change_rate)}")
        logging.info("=" * 70 + "\n")

        return float(profit_rate), float(coin_change_rate)

    def run_backTest(self, ticker: str, interval: str,
                     start_time: datetime, end_time: datetime,
                     display_chart: bool = False) -> PeriodResult:
        """백테스트 실행 (기존 인터페이스 호환성 유지, PeriodResult 반환)"""
        self._reset_state()
        data = self._prepare_data(ticker, interval, start_time, end_time)

        if data.empty:
            logging.warning(f"데이터가 없습니다: {ticker}, {interval}, {start_time} ~ {end_time}")
            return PeriodResult(0.0, 0.0, 0.0, 0.0)

        self._process_trading_data(data)

        # 미체결 코인 청산
        if self.state.coin_quantity > 0:
            final_price = Decimal(str(data.iloc[-1]['close']))
            final_timestamp = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
            self.execute_sell(final_price, final_timestamp, force=True)

        profit_rate, coin_change_rate = self.display_account_summary(ticker, interval, start_time, end_time)

        if display_chart:
            self._display_chart(data)

        return PeriodResult(
            trading_profit=profit_rate,
            coin_change_rate=coin_change_rate,
            start_price=float(self.state.start_price),
            end_price=float(self.state.end_price)
        )

    def _reset_state(self) -> None:
        """상태 초기화"""
        self.state = TradingState(
            balance=self.config.INITIAL_BALANCE,
            coin_quantity=Decimal('0'),
            min_price=Decimal('0'),
            max_price=Decimal('0'),
            start_price=Decimal('0'),
            end_price=Decimal('0')
        )
        self.result = TradingResult()

    def _prepare_data(self, ticker: str, interval: str,
                      start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """거래 데이터 준비"""
        return db.make_tick_db(start_time, end_time, ticker, interval)

    def _process_trading_data(self, data: pd.DataFrame) -> None:
        """거래 데이터 처리"""
        for i in range(len(data)):
            try:
                price = Decimal(str(data.iloc[i]['close']))
                timestamp = data.index[i] if hasattr(data.index[i], 'to_pydatetime') else datetime.now()

                if i == 0:
                    self.state.start_price = price
                elif i == len(data) - 1:
                    self.state.end_price = price

                # RSI 데이터가 없는 경우 건너뛰기
                if 'rsi_k' in data.columns and 'rsi_d' in data.columns:
                    if pd.isna(data.iloc[i]['rsi_k']) or pd.isna(data.iloc[i]['rsi_d']):
                        self._append_no_trade()
                        continue

                    self._process_trading_signals(data, i, price, timestamp)
                else:
                    # RSI 데이터가 없는 경우 기본 로직으로 처리
                    self._process_basic_trading_signals(data, i, price, timestamp)

            except (KeyError, ValueError, IndexError) as e:
                logging.debug(f"데이터 처리 오류 (인덱스 {i}): {str(e)}")
                self._append_no_trade()
                continue

    def _process_trading_signals(self, data: pd.DataFrame, index: int,
                                 price: Decimal, timestamp: datetime) -> None:
        """거래 신호 처리 (RSI 포함)"""
        try:
            rsi_k = data.iloc[index]['rsi_k']
            rsi_d = data.iloc[index]['rsi_d']
            signal = data.iloc[index]['signal'] if 'signal' in data.columns else 0

            if ((rsi_k > rsi_d) and (rsi_k < self.config.RSI_OVERSOLD) and
                    signal > 0):
                self.execute_buy(price, timestamp, data=data, current_index=index)
            elif ((rsi_k < rsi_d) and (rsi_k > self.config.RSI_OVERBOUGHT) and
                  signal < 0):
                self.execute_sell(price, timestamp, data=data, current_index=index)
            else:
                self._append_no_trade()
        except Exception as e:
            logging.debug(f"RSI 신호 처리 오류: {str(e)}")
            self._append_no_trade()

    def _process_basic_trading_signals(self, data: pd.DataFrame, index: int,
                                       price: Decimal, timestamp: datetime) -> None:
        """기본 거래 신호 처리 (RSI 없이)"""
        # RSI 데이터가 없는 경우 엘리어트 파동 분석만으로 거래
        if index > ELLIOTT_WAVE_PATTERN_LENGTH:
            elliott_analysis = enhanced_elliott_analysis(data, index)

            if elliott_analysis['buy_signal_strength'] >= 40:
                self.execute_buy(price, timestamp, data=data, current_index=index)
            elif elliott_analysis['sell_signal_strength'] >= 40:
                self.execute_sell(price, timestamp, data=data, current_index=index)
            else:
                self._append_no_trade()
        else:
            self._append_no_trade()

    @staticmethod
    def _display_chart(data: pd.DataFrame) -> None:
        """차트 표시"""
        try:
            dw.display_rsi(data)
        except Exception as e:
            logging.warning(f"차트 표시 오류: {str(e)}")


# === Main Execution ===
def main():
    """메인 실행 함수"""
    # 거래 설정
    trading_config = TradingConfig(
        INITIAL_BALANCE=Decimal('10000000'),
        MIN_PRICE_CHANGE_RATE=Decimal('1.01'),
        MAX_PRICE_CHANGE_RATE=Decimal('1.01'),
        RSI_OVERSOLD=30,
        RSI_OVERBOUGHT=70,
        DISPLAY_CHART=False,
        TRADING_FEE=Decimal('0.0005')
    )

    back_tester = BackTest(trading_config)
    tickers = TRADING_CONFIG['tickers']
    intervals = TRADING_CONFIG['time_intervals']
    display_chart = False

    # 테스트할 기간 생성
    trading_periods = get_selected_periods(TRADING_CONFIG)

    # 결과 저장 구조 초기화
    trading_results = initialize_results_structure(tickers, trading_periods)

    logging.info("=" * 50)
    logging.info("백테스트 시작")
    logging.info("=" * 50)
    logging.info(f"초기 자본금: {format_currency(trading_config.INITIAL_BALANCE)}")
    logging.info(f"거래 수수료율: {trading_config.TRADING_FEE * 100}%")
    logging.info(f"테스트 코인: {', '.join(tickers)}")
    logging.info(f"테스트 간격: {', '.join(intervals)}분")
    logging.info(f"테스트 기간: {len(trading_periods)}개 기간")
    logging.info("=" * 50)

    # 백테스트 실행
    total_tests = len(tickers) * len(trading_periods) * len(intervals)
    current_test = 0

    for ticker in tickers:
        logging.info(f"\n{ticker} 백테스트 진행중...")
        ticker_start_time = datetime.now()

        for period in trading_periods:
            for interval in intervals:
                current_test += 1
                try:
                    logging.info(f"진행률: {current_test}/{total_tests} - {ticker} {period.year}-{period.month}")

                    result = back_tester.run_backTest(
                        ticker,
                        interval,
                        period.start,
                        period.end,
                        display_chart
                    )
                    trading_results[ticker][period.year][period.month] = result

                except Exception as e:
                    logging.error(f"오류 발생: {ticker} {period.year}-{period.month} - {str(e)}")
                    trading_results[ticker][period.year][period.month] = PeriodResult(0, 0, 0, 0)

        ticker_end_time = datetime.now()
        ticker_duration = ticker_end_time - ticker_start_time
        logging.info(f"{ticker} 완료 (소요시간: {ticker_duration})")

    # 결과 출력
    logging.info("\n" + "=" * 50)
    logging.info("백테스트 완료")
    logging.info("=" * 50)
    print_trading_results(trading_results)

    # 추가 통계 출력
    logging.info("=== 상세 통계 ===")
    for ticker, yearly_data in trading_results.items():
        profitable_months = 0
        total_months = 0
        total_trading_profit = 0
        total_coin_change = 0

        for year, monthly_data in yearly_data.items():
            for month, period_result in monthly_data.items():
                if isinstance(period_result, PeriodResult):
                    total_months += 1
                    total_trading_profit += period_result.trading_profit
                    total_coin_change += period_result.coin_change_rate

                    if period_result.trading_profit > 0:
                        profitable_months += 1

        win_rate = (profitable_months / total_months * 100) if total_months > 0 else 0
        avg_trading_profit = total_trading_profit / total_months if total_months > 0 else 0
        avg_coin_change = total_coin_change / total_months if total_months > 0 else 0
        alpha = avg_trading_profit - avg_coin_change  # 알파 (시장 대비 초과 수익)

        logging.info(f"\n[{ticker} 요약]")
        logging.info(f"승률: {win_rate:.1f}% ({profitable_months}/{total_months})")
        logging.info(f"평균 거래수익률: {avg_trading_profit:+.2f}%")
        logging.info(f"평균 코인변동률: {avg_coin_change:+.2f}%")
        logging.info(f"알파 (초과수익): {alpha:+.2f}%p")

        if avg_coin_change != 0:
            sharpe_like_ratio = avg_trading_profit / abs(avg_coin_change)
            logging.info(f"수익 효율성: {sharpe_like_ratio:.2f}")

def run_specific_period_backtest():
    """특정 임의의 기간에 대해 백테스트 실행"""
    # 거래 설정 생성
    trading_config = TradingConfig(
        INITIAL_BALANCE=Decimal('10000000'),  # 초기 자본금: 10,000,000 KRW
        MIN_PRICE_CHANGE_RATE=Decimal('1.01'),
        MAX_PRICE_CHANGE_RATE=Decimal('1.01'),
        RSI_OVERSOLD=30,
        RSI_OVERBOUGHT=70,
        DISPLAY_CHART=False,
        TRADING_FEE=Decimal('0.0005')
    )

    # 지정한 설정으로 BackTest 객체 생성
    back_tester = BackTest(trading_config)

    # 특정 기간 입력 받기
    ticker = input("백테스트할 코인을 입력하세요 (예: KRW-ETH): ")
    interval = input("테스트할 간격(분)을 입력하세요 (예: 60): ")
    start_date = input("테스트 시작 날짜를 입력하세요 (예: 2023-01-01): ")
    end_date = input("테스트 종료 날짜를 입력하세요 (예: 2023-12-31): ")

    try:
        # 날짜를 파싱
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

        # 실행
        result = back_tester.run_backTest(
            ticker=ticker,
            interval=interval,
            start_time=start_datetime,
            end_time=end_datetime,
            display_chart=False
        )

        # 결과 출력
        print("\n[결과]")
        print(f"수익률: {result.trading_profit:.2f}%")
        print(f"코인 변동률: {result.coin_change_rate:.2f}%")
        print(f"시작가: {result.start_price}")
        print(f"종료가: {result.end_price}")
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == '__main__':
    #main()
    run_specific_period_backtest()
