from decimal import Decimal
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import sys

# 파일 최상단의 import 부분 아래에 추가
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)

@dataclass
class TradingConfig:
    """거래 설정을 위한 데이터 클래스"""
    INITIAL_BALANCE: Decimal
    MIN_PRICE_CHANGE_RATE: Decimal
    MAX_PRICE_CHANGE_RATE: Decimal
    RSI_OVERSOLD: int
    RSI_OVERBOUGHT: int
    DISPLAY_CHART: bool
    TRADING_FEE: Decimal

def format_currency(amount: Decimal) -> str:
    """통화 형식으로 포맷팅"""
    return f"{amount:,.0f} KRW"

def format_percentage(value: Decimal) -> str:
    """백분율 형식으로 포맷팅"""
    return f"{value:.2f}%"

class BackTest:
    def __init__(self):
        self.balance = Decimal('0')
        
    def run_backTest(self, ticker: str, interval: str, 
                    start_date: datetime, end_date: datetime, 
                    display_chart: bool) -> Decimal:
        # 백테스트 로직 구현
        # 임시로 랜덤한 수익률 반환
        import random
        return Decimal(str(random.uniform(-10, 10)))

# run_period_backtest 함수에서 다음과 같이 수정
def run_period_backtest(config: TradingConfig,
                       periods: Dict[int, List[int]],
                       tickers: List[str],
                       intervals: List[str]) -> Dict[str, Dict[int, Dict[int, Decimal]]]:
    results: Dict[str, Dict[int, Dict[int, Decimal]]] = {}
    
    for ticker in tickers:
        results[ticker] = {}
        for year in periods:
            results[ticker][year] = {}
            for month in periods[year]:
                # BackTest로 클래스명 수정
                bt = BackTest()
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
                
                profit = Decimal('0')
                for interval in intervals:
                    profit = bt.run_backTest(ticker, interval, start_date, end_date, config.DISPLAY_CHART)
                
                results[ticker][year][month] = profit
    
    return results

def analyze_and_print_results(results: Dict[str, Dict[int, Dict[int, Decimal]]]) -> None:
    """백테스트 결과 분석 및 출력"""
    logging.info("\n=== 백테스트 결과 요약 ===")

    total_stats: Dict[str, Any] = {  # type: ignore
        'total_profit': Decimal('0'),
        'best_profit': (None, None, None, Decimal('-999999')),  # (year, month, ticker, profit)
        'worst_profit': (None, None, None, Decimal('999999')),  # (year, month, ticker, profit)
        'profitable_months': 0,
        'total_months': 0
    }

    for ticker in results:
        ticker_total_profit = Decimal('0')
        ticker_months = 0

        logging.info(f"\n[{ticker}]")
        logging.info("-" * 40)

        for year in sorted(results[ticker].keys()):
            yearly_profit = Decimal('0')

            logging.info(f"\n{year}년:")
            for month in sorted(results[ticker][year].keys()):
                profit = results[ticker][year][month]
                yearly_profit += profit
                ticker_total_profit += profit
                ticker_months += 1

                if profit > total_stats['best_profit'][3]:
                    total_stats['best_profit'] = (year, month, ticker, profit)
                if profit < total_stats['worst_profit'][3]:
                    total_stats['worst_profit'] = (year, month, ticker, profit)

                if profit > 0:
                    total_stats['profitable_months'] += 1

                month_name = f"{month}월".rjust(4)
                profit_str = f"{format_percentage(profit)}".rjust(10)
                logging.info(f"{month_name}: {profit_str}")

            logging.info(f"연간 합계: {format_percentage(yearly_profit)}")

        avg_monthly_profit = ticker_total_profit / Decimal(str(ticker_months)) if ticker_months > 0 else Decimal('0')
        logging.info(f"\n{ticker} 총 수익률: {format_percentage(ticker_total_profit)}")
        logging.info(f"{ticker} 월평균 수익률: {format_percentage(avg_monthly_profit)}")

        total_stats['total_profit'] += ticker_total_profit
        total_stats['total_months'] += ticker_months

    # 전체 통계 출력
    print_total_stats(total_stats)

def print_total_stats(total_stats: Dict[str, Any]) -> None:  # type: ignore
    """전체 통계 출력"""
    logging.info("\n=== 전체 통계 ===")
    logging.info(f"총 수익률: {format_percentage(total_stats['total_profit'])}")
    
    avg_monthly = (total_stats['total_profit'] / Decimal(str(total_stats['total_months']))
                  if total_stats['total_months'] > 0 else Decimal('0'))
    logging.info(f"전체 월평균 수익률: {format_percentage(avg_monthly)}")

    win_rate = (Decimal(str(total_stats['profitable_months'])) /
               Decimal(str(total_stats['total_months'])) * Decimal('100')
               if total_stats['total_months'] > 0 else Decimal('0'))
    logging.info(f"수익 발생 비율: {format_percentage(win_rate)}")

    print_best_worst_stats(total_stats)

def print_best_worst_stats(total_stats: Dict[str, Any]) -> None:  # type: ignore
    """최고/최저 수익 통계 출력"""
    best_year, best_month, best_ticker, best_profit = total_stats['best_profit']
    worst_year, worst_month, worst_ticker, worst_profit = total_stats['worst_profit']

    if best_year is not None:
        logging.info("\n[최고 수익]")
        logging.info(f"코인: {best_ticker}")
        logging.info(f"기간: {best_year}년 {best_month}월")
        logging.info(f"수익률: {format_percentage(best_profit)}")

    if worst_year is not None:
        logging.info("\n[최저 수익]")
        logging.info(f"코인: {worst_ticker}")
        logging.info(f"기간: {worst_year}년 {worst_month}월")
        logging.info(f"수익률: {format_percentage(worst_profit)}")

def main() -> None:
    """
    메인 실행 함수
    백테스트 설정, 실행 및 결과 분석을 관리
    """
    # === 백테스트 설정 ===
    trading_config = TradingConfig(
        INITIAL_BALANCE=Decimal('10000000'),
        MIN_PRICE_CHANGE_RATE=Decimal('1.01'),
        MAX_PRICE_CHANGE_RATE=Decimal('1.01'),
        RSI_OVERSOLD=30,
        RSI_OVERBOUGHT=70,
        DISPLAY_CHART=False,
        TRADING_FEE=Decimal('0.0005')
    )

    # 테스트 기간 설정
    test_periods = {
        2024: list(range(6, 13)),  # 전체 월
    }

    # 테스트할 티커와 인터벌
    test_config = {
        # 'tickers': ['KRW-ETH', 'KRW-XRP'],
        'tickers': ['KRW-ETH'],
        'intervals': ['240'],  # 1시간 간격
        'display_chart': False
    }

    try:
        logging.info("\n=== 백테스트 시작 ===")
        logging.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("\n[테스트 설정]")
        logging.info(f"초기 자본금: {format_currency(trading_config.INITIAL_BALANCE)}")
        logging.info(f"거래 수수료율: {trading_config.TRADING_FEE * Decimal('100')}%")
        logging.info(f"테스트 기간: {test_periods}")
        logging.info(f"대상 코인: {', '.join(test_config['tickers'])}")
        logging.info(f"거래 간격: {', '.join(test_config['intervals'])}분")

        # === 백테스트 실행 ===
        results = run_period_backtest(
            config=trading_config,
            periods=test_periods,
            tickers=test_config['tickers'],
            intervals=test_config['intervals']
        )

        # === 결과 분석 및 출력 ===
        analyze_and_print_results(results)

    except Exception as e:
        logging.error(f"\n오류 발생: {str(e)}")
        logging.exception("상세 오류 정보:")
    finally:
        logging.info(f"\n종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=== 백테스트 종료 ===\n")

if __name__ == "__main__":
    main()