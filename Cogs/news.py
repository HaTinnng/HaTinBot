import os
import random
import discord
from discord.ext import commands, tasks
from datetime import datetime
import pytz
from pymongo import MongoClient

# 데이터베이스 설정 (기존 코드와 동일)
DB_NAME = "stock_game"
MONGO_URI = os.environ.get("MONGODB_URI")

class StockNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # MongoDB 연결
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]
        # 최신 뉴스 목록 (각 뉴스 항목은 headline과 details를 포함)
        self.current_news = []
        # 마지막 뉴스 업데이트 분 기록 (중복 업데이트 방지용)
        self.last_news_min = None
        # 뉴스 업데이트 루프 시작 (10초마다 실행)
        self.news_update_loop.start()

    def cog_unload(self):
        self.news_update_loop.cancel()
        self.mongo_client.close()

    @tasks.loop(seconds=10)
    async def news_update_loop(self):
        """
        매 10초마다 현재 시각의 분(minute)이 0, 20, 40분 중 하나인지 확인하고,
        해당 분에 아직 뉴스가 생성되지 않았다면 새로운 뉴스를 생성합니다.
        """
        now = datetime.now(pytz.timezone("Asia/Seoul"))
        if now.minute in [0, 20, 40] and self.last_news_min != now.minute:
            self.generate_news()
            self.last_news_min = now.minute

    def generate_news(self):
        """
        DB의 상장된 주식 종목 중에서 무작위로 몇 종목을 선택하고,
        다양한 뉴스 템플릿을 바탕으로 헤드라인과 상세 설명을 생성합니다.
        모든 문구에서 실제 변동 대신 "예상됩니다"라는 표현을 사용합니다.
        """
        stocks = list(self.db.stocks.find({"listed": True}))
        if not stocks:
            self.current_news = [{"headline": "현재 뉴스가 없습니다.", "details": ""}]
            return

        # 총 75개의 뉴스 템플릿 (기존 25개 + 추가 20개 + 추가 30개)
        news_templates = [
            # 기존 25개 템플릿
            {"type": "positive", "headline": "{stock}의 주가가 상승세를 보일 것으로 예상됩니다.", "details": "최근 투자자들의 긍정적인 분위기와 거래량 증가를 바탕으로, {stock}의 주가가 상승세를 보일 것으로 예상됩니다. 전문가들은 이 추세가 지속될 것으로 전망됩니다."},
            {"type": "negative", "headline": "{stock}의 주가가 급락할 것으로 예상됩니다.", "details": "최근 발생한 부정적 이슈와 시장 불안으로 인해, {stock}의 주가가 급락할 것으로 예상됩니다. 투자자들은 추가 하락 가능성에 대비해야 할 것으로 보입니다."},
            {"type": "neutral", "headline": "{stock} 관련 시장 동향에 변화가 예상됩니다.", "details": "{stock}에 대한 시장의 반응이 다양하게 나타날 것으로 예상됩니다. 일부는 긍정, 일부는 부정의 신호를 보내고 있어 투자자들의 신중한 판단이 요구됩니다."},
            {"type": "in-depth_positive", "headline": "{stock}의 최신 분기 실적이 호조를 보일 것으로 예상됩니다.", "details": "{stock}이 발표할 예정인 최신 분기 실적이 시장 예상치를 상회할 것으로 예상되며, 투자자들의 기대감이 커지고 있습니다."},
            {"type": "in-depth_negative", "headline": "{stock}의 경영진이 실적 부진에 대해 해명할 것으로 예상됩니다.", "details": "최근 {stock}의 실적 부진과 관련해 경영진이 곧 해명을 발표할 것으로 예상되며, 이에 따른 주가 변동에 대한 우려가 제기됩니다."},
            {"type": "analysis", "headline": "전문가들은 {stock}의 단기 주가 변동이 불안정할 것으로 예상됩니다.", "details": "최근 시장 분석에 따르면, {stock}의 주가가 단기적으로 불안정한 움직임을 보일 것으로 예상되며, 투자자들은 리스크 관리에 신경 써야 합니다."},
            {"type": "sentiment_negative", "headline": "투자 심리가 {stock}에 부정적인 영향을 미칠 것으로 예상됩니다.", "details": "최근 투자 심리 위축과 불안감으로 인해, {stock}의 주가가 하락할 것으로 예상되며, 시장의 반응에 주목할 필요가 있습니다."},
            {"type": "sentiment_positive", "headline": "{stock}의 주가가 거래량 급증과 함께 상승할 것으로 예상됩니다.", "details": "최근 거래량 증가가 {stock}의 긍정적인 주가 상승 신호로 해석되며, 전문가들은 이를 주가 상승 요인으로 보고 있습니다."},
            {"type": "interest", "headline": "{stock}에 대한 투자자들의 관심이 증가할 것으로 예상됩니다.", "details": "시장 조사에 따르면, {stock}의 독특한 성장 전략이 투자자들의 관심을 끌어올릴 것으로 예상됩니다."},
            {"type": "product", "headline": "{stock}의 신제품 발표가 주가에 긍정적 영향을 줄 것으로 예상됩니다.", "details": "다가오는 신제품 발표 소식에 힘입어, {stock}의 주가가 상승할 것으로 예상되며, 투자자들의 기대감이 높아지고 있습니다."},
            {"type": "global", "headline": "{stock}의 글로벌 시장 진출이 주가를 견인할 것으로 예상됩니다.", "details": "글로벌 시장 확장을 위한 {stock}의 전략이 주가에 긍정적인 영향을 미칠 것으로 예상되며, 장기적인 성장 가능성이 주목됩니다."},
            {"type": "volatility", "headline": "최근 분석 결과, {stock}의 주가가 변동성을 보일 것으로 예상됩니다.", "details": "시장 전문가들은 {stock}이 단기적으로 큰 변동성을 보일 것으로 예상하고 있으며, 투자자들은 변동성에 대비해야 합니다."},
            {"type": "earnings", "headline": "{stock}의 실적 발표 이후 주가에 변동이 있을 것으로 예상됩니다.", "details": "곧 발표될 {stock}의 실적에 따라 주가가 크게 움직일 것으로 예상되며, 투자자들의 주의가 요구됩니다."},
            {"type": "trade", "headline": "{stock}의 주가가 최근 거래 호조에 힘입어 상승할 것으로 예상됩니다.", "details": "거래 호조와 긍정적 투자 분위기가 {stock}의 주가 상승을 이끌 것으로 예상되며, 이는 시장 전반에 긍정적인 신호를 줄 것으로 보입니다."},
            {"type": "uncertainty", "headline": "시장 불안정 속에서 {stock}의 주가가 하락할 것으로 예상됩니다.", "details": "불안정한 글로벌 경제 상황과 내부 이슈로 인해, {stock}의 주가가 단기적으로 하락할 것으로 예상됩니다."},
            {"type": "innovation", "headline": "{stock}의 기술 혁신 소식이 주가에 긍정적 영향을 줄 것으로 예상됩니다.", "details": "최근 발표된 기술 혁신 소식이 {stock}의 경쟁력을 강화할 것으로 기대되며, 주가 상승이 예상됩니다."},
            {"type": "competition", "headline": "{stock}의 주요 경쟁사와의 비교 분석 결과, 주가에 조정이 있을 것으로 예상됩니다.", "details": "경쟁사 대비 {stock}의 위치와 성장 가능성에 대한 분석이 주가에 반영될 것으로 예상되며, 투자자들은 변동에 주의해야 합니다."},
            {"type": "strategy", "headline": "{stock}의 경영 전략 변화가 주가에 영향을 미칠 것으로 예상됩니다.", "details": "최근 발표된 경영 전략 변화가 {stock}의 미래 주가에 큰 영향을 줄 것으로 예상되며, 시장의 반응이 주목되고 있습니다."},
            {"type": "psychology", "headline": "투자자 심리 변화로 {stock}의 주가가 조정될 것으로 예상됩니다.", "details": "최근 투자자 심리 변화에 따라 {stock}의 주가가 일시적으로 조정될 것으로 예상되며, 이는 단기적인 현상으로 볼 수 있습니다."},
            {"type": "investment", "headline": "{stock}의 신규 투자 소식이 주가를 견인할 것으로 예상됩니다.", "details": "대규모 신규 투자가 발표됨에 따라, {stock}의 주가가 상승할 것으로 예상되며, 투자자들의 기대감이 높아지고 있습니다."},
            {"type": "stability", "headline": "{stock}의 주가가 시장 전반의 불확실성 속에서도 안정세를 보일 것으로 예상됩니다.", "details": "불확실한 시장 상황에도 불구하고, {stock}의 견고한 재무 구조가 주가를 안정시킬 것으로 예상됩니다."},
            {"type": "issue", "headline": "최근 이슈로 인해 {stock}의 주가가 일시적으로 하락할 것으로 예상됩니다.", "details": "특정 이슈로 인해 {stock}의 주가가 단기적으로 하락할 것으로 예상되나, 장기적으로는 회복할 가능성이 제기됩니다."},
            {"type": "overseas", "headline": "{stock}의 해외 시장 진출 소식이 주가에 긍정적 영향을 줄 것으로 예상됩니다.", "details": "해외 시장 진출 계획이 발표됨에 따라 {stock}의 주가가 상승할 것으로 예상되며, 이는 글로벌 확장의 신호로 해석됩니다."},
            {"type": "internal", "headline": "{stock}의 주가가 내부 이슈 해결에 따른 기대감으로 상승할 것으로 예상됩니다.", "details": "최근 내부 이슈가 해결될 조짐을 보이면서, {stock}의 주가가 긍정적인 방향으로 조정될 것으로 예상됩니다."},
            {"type": "adjustment", "headline": "전문가들은 {stock}의 주가가 단기적으로 조정 국면에 들어설 것으로 예상됩니다.", "details": "단기적인 조정 국면에 진입할 것으로 예상되지만, {stock}의 장기적인 성장 전망은 여전히 긍정적이라는 평가가 있습니다."},
            # 추가 20개 템플릿
            {"type": "merger", "headline": "{stock}의 합병 소식이 시장에 큰 반향을 불러일으킬 것으로 예상됩니다.", "details": "최근 {stock}과 관련된 합병 소식이 투자자들의 관심을 모으고 있으며, 이번 합병이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다."},
            {"type": "dividend", "headline": "{stock}의 배당 정책 변화가 주가에 영향을 미칠 것으로 예상됩니다.", "details": "최근 발표된 {stock}의 배당 정책 변화가 투자자들에게 긍정적인 신호로 작용할 것으로 예상되며, 주가 상승의 요인으로 평가됩니다."},
            {"type": "regulation", "headline": "정부 규제 변화로 {stock}의 주가에 변동이 있을 것으로 예상됩니다.", "details": "최근 정부의 규제 변화가 {stock}에 직접적인 영향을 미칠 것으로 예상되며, 이로 인한 주가 변동에 주의가 요구됩니다."},
            {"type": "scandal", "headline": "{stock} 관련 내부 스캔들이 주가에 부정적인 영향을 미칠 것으로 예상됩니다.", "details": "최근 {stock}과 관련된 내부 스캔들 소식이 전해지면서, 투자자들의 불안이 증폭되고 주가 하락이 예상됩니다."},
            {"type": "innovation_tech", "headline": "{stock}의 AI 도입 소식이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "최근 AI 기술 도입에 따른 {stock}의 혁신적인 변화가 시장에서 주목받고 있으며, 주가 상승에 기여할 것으로 예상됩니다."},
            {"type": "market_expansion", "headline": "{stock}의 새로운 시장 진출이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "국내외 새로운 시장 진출 계획이 발표된 {stock}의 주가가 이를 반영하여 상승할 것으로 예상됩니다."},
            {"type": "financial_results", "headline": "{stock}의 재무 지표 개선 소식이 주가에 긍정적으로 작용할 것으로 예상됩니다.", "details": "최근 {stock}의 재무 지표가 개선되면서 투자자들의 신뢰가 회복되고, 주가 상승 기대감이 높아지고 있습니다."},
            {"type": "supply_chain", "headline": "{stock}의 공급망 안정화 소식이 주가 상승에 기여할 것으로 예상됩니다.", "details": "공급망 문제가 해소된 {stock}이 안정적인 생산과 유통을 기대하게 하여 주가 상승 요인으로 작용할 것으로 예상됩니다."},
            {"type": "research", "headline": "새로운 연구 결과가 {stock}의 성장 가능성을 높일 것으로 예상됩니다.", "details": "최근 발표된 연구 결과가 {stock}의 기술 및 시장 지위를 강화할 것으로 예상되며, 주가에 긍정적인 영향을 미칠 것으로 보입니다."},
            {"type": "leadership", "headline": "{stock}의 경영진 교체 소식이 주가에 영향을 미칠 것으로 예상됩니다.", "details": "경영진 교체와 관련된 소식이 전해지면서, {stock}의 경영 전략이 재정비될 것으로 예상되며, 이에 따른 주가 변동이 예상됩니다."},
            {"type": "market_sentiment", "headline": "시장 전반의 긍정적인 분위기가 {stock}의 주가 상승을 견인할 것으로 예상됩니다.", "details": "전반적인 시장 심리가 개선됨에 따라, {stock}에 대한 투자자들의 신뢰가 높아지고 주가 상승이 예상됩니다."},
            {"type": "partnership", "headline": "{stock}의 전략적 제휴 소식이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "최근 {stock}이 발표한 전략적 제휴 소식이 투자자들에게 긍정적으로 받아들여져, 주가 상승에 기여할 것으로 예상됩니다."},
            {"type": "merger_2", "headline": "{stock}의 인수합병 움직임이 시장에 큰 파장을 일으킬 것으로 예상됩니다.", "details": "최근 {stock}과 관련된 인수합병 관련 소식이 전해지면서, 투자자들이 이에 주목하고 있으며, 주가 변동성이 커질 것으로 예상됩니다."},
            {"type": "economic", "headline": "글로벌 경제 상황 변화가 {stock}의 주가에 영향을 미칠 것으로 예상됩니다.", "details": "최근 발표된 경제 지표 변화가 {stock}의 산업 환경에 영향을 미칠 것으로 예상되며, 주가 변동에 주의가 요구됩니다."},
            {"type": "innovation_fintech", "headline": "{stock}의 핀테크 혁신이 금융 시장에 긍정적으로 작용할 것으로 예상됩니다.", "details": "최신 핀테크 솔루션 도입으로 {stock}의 운영 효율성이 향상될 것으로 예상되며, 주가 상승 기대감이 커지고 있습니다."},
            {"type": "customer", "headline": "{stock}의 고객 서비스 개선이 주가에 긍정적 영향을 미칠 것으로 예상됩니다.", "details": "최근 고객 만족도 향상 정책이 발표된 {stock}이 투자자들의 신뢰를 얻어 주가 상승 요인으로 작용할 것으로 예상됩니다."},
            {"type": "innovation_research", "headline": "{stock}의 연구개발 투자 확대가 장기적 성장에 기여할 것으로 예상됩니다.", "details": "연구개발에 대한 {stock}의 투자 확대가 기술 혁신과 경쟁력 강화로 이어질 것으로 예상되며, 장기적으로 주가 상승이 기대됩니다."},
            {"type": "stock_split", "headline": "{stock}의 주식 분할 계획이 투자자들에게 긍정적으로 작용할 것으로 예상됩니다.", "details": "주식 분할 계획 발표가 {stock}에 대한 접근성을 높여 투자자들의 관심을 끌 것으로 예상되며, 주가 상승에 영향을 미칠 것으로 예상됩니다."},
            {"type": "insider_trading", "headline": "{stock} 내부자의 거래 소식이 주가에 단기적인 영향을 미칠 것으로 예상됩니다.", "details": "최근 {stock} 내부자의 주식 거래 소식이 전해지면서, 단기적인 주가 변동이 예상되나 장기적인 영향은 미미할 것으로 예상됩니다."},
            {"type": "seasonal", "headline": "계절적 요인에 따라 {stock}의 주가가 조정될 것으로 예상됩니다.", "details": "계절적 수요 변화와 관련된 분석 결과가 발표되면서, {stock}의 주가가 단기적으로 조정될 것으로 예상되며, 이는 일시적인 현상으로 보입니다."},
            # 추가 30개 템플릿
            {"type": "tech", "headline": "{stock}의 AI 도입 소식이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "최근 AI 기술 도입에 따른 {stock}의 혁신적인 변화가 시장에서 주목받고 있으며, 주가 상승에 기여할 것으로 예상됩니다."},
            {"type": "sustainability", "headline": "{stock}의 친환경 경영 전략이 주가에 긍정적인 효과를 줄 것으로 예상됩니다.", "details": "환경 친화적 정책을 강화하는 {stock}이 투자자들의 관심을 끌고 있으며, 장기적으로 주가 안정에 기여할 것으로 예상됩니다."},
            {"type": "expansion", "headline": "{stock}의 해외 지사 확장이 주가 상승을 견인할 것으로 예상됩니다.", "details": "해외 지사 확장 계획이 발표됨에 따라 {stock}의 글로벌 경쟁력이 강화되고, 주가 상승에 긍정적으로 작용할 것으로 예상됩니다."},
            {"type": "innovation_biotech", "headline": "{stock}의 바이오 기술 혁신이 투자자들의 기대를 모을 것으로 예상됩니다.", "details": "최신 바이오 기술 도입과 연구 성과가 {stock}의 성장 동력으로 작용할 것으로 예상되며, 주가 상승이 기대됩니다."},
            {"type": "expensive", "headline": "{stock}의 고가 정책이 시장에서 논란이 될 것으로 예상됩니다.", "details": "고가 전략이 {stock}의 매출에 영향을 미칠 것으로 예상되며, 이에 따른 주가 변동성이 커질 것으로 예상됩니다."},
            {"type": "partnership_2", "headline": "{stock}과(와) 주요 기업 간의 제휴가 주가 상승에 기여할 것으로 예상됩니다.", "details": "최근 {stock}과 주요 기업 간의 전략적 제휴가 체결되면서, 주가에 긍정적인 영향이 미칠 것으로 예상됩니다."},
            {"type": "market_demand", "headline": "{stock}의 제품 수요 증가가 주가 상승을 부추길 것으로 예상됩니다.", "details": "시장 내 {stock}의 제품에 대한 수요 증가가 주가 상승 요인으로 작용할 것으로 예상되며, 이는 긍정적인 투자 신호로 평가됩니다."},
            {"type": "trade_volume", "headline": "{stock}의 거래량 증가가 주가에 긍정적인 모멘텀을 제공할 것으로 예상됩니다.", "details": "거래량이 급증함에 따라 {stock}의 주가가 단기적으로 상승할 것으로 예상되며, 투자자들의 관심이 집중될 것으로 예상됩니다."},
            {"type": "innovation_retail", "headline": "{stock}의 소매 혁신 전략이 주가 상승에 기여할 것으로 예상됩니다.", "details": "소매 업계에서의 혁신적인 전략이 {stock}의 경쟁력을 높여주며, 주가 상승에 긍정적인 영향을 미칠 것으로 예상됩니다."},
            {"type": "brand_value", "headline": "{stock}의 브랜드 가치 상승이 주가에 반영될 것으로 예상됩니다.", "details": "강력한 브랜드 인지도와 가치 상승이 {stock}의 주가를 견인할 것으로 예상되며, 이는 장기적인 성장의 신호로 평가됩니다."},
            {"type": "corporate_governance", "headline": "{stock}의 기업 거버넌스 개선이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "투명한 경영 체제와 기업 거버넌스 개선이 {stock}의 신뢰도를 높여 주가 상승에 기여할 것으로 예상됩니다."},
            {"type": "risky", "headline": "{stock}의 신규 사업 진출이 단기적으로 위험 요소로 작용할 것으로 예상됩니다.", "details": "신규 사업 진출로 인한 불확실성이 {stock}의 주가에 부정적인 영향을 미칠 수 있으나, 장기적으로는 성장 동력으로 작용할 것으로 예상됩니다."},
            {"type": "supply_demand", "headline": "{stock}의 공급과 수요 불균형이 주가에 변동을 줄 것으로 예상됩니다.", "details": "공급 부족 및 수요 증가가 동시에 발생할 것으로 예상되어, {stock}의 주가가 단기적으로 변동될 것으로 예상됩니다."},
            {"type": "new_contract", "headline": "{stock}의 신규 계약 체결 소식이 주가에 긍정적인 모멘텀을 제공할 것으로 예상됩니다.", "details": "최근 {stock}이 중요한 신규 계약을 체결하면서, 주가 상승 기대감이 형성될 것으로 예상됩니다."},
            {"type": "cost_cutting", "headline": "{stock}의 비용 절감 정책이 주가에 긍정적으로 작용할 것으로 예상됩니다.", "details": "효율적인 비용 절감 전략이 {stock}의 수익성을 개선하여, 주가 상승에 기여할 것으로 예상됩니다."},
            {"type": "market_share", "headline": "{stock}의 시장 점유율 확대가 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "시장 점유율 확대가 {stock}의 경쟁력을 강화할 것으로 예상되며, 이에 따른 주가 상승이 기대됩니다."},
            {"type": "innovation_ecommerce", "headline": "{stock}의 전자상거래 혁신이 주가 상승에 기여할 것으로 예상됩니다.", "details": "전자상거래 부문에서의 혁신적인 전략이 {stock}의 매출 증대로 이어져, 주가 상승 기대감이 형성될 것으로 예상됩니다."},
            {"type": "economic_policy", "headline": "정부의 경제 정책 변화가 {stock}의 주가에 영향을 미칠 것으로 예상됩니다.", "details": "최근 발표된 경제 정책이 {stock}의 산업 환경에 영향을 미칠 것으로 예상되며, 주가 변동에 주의가 요구됩니다."},
            {"type": "foreign_investment", "headline": "{stock}에 대한 해외 투자자들의 관심이 주가에 긍정적으로 작용할 것으로 예상됩니다.", "details": "해외 투자자들의 관심이 증가함에 따라, {stock}의 주가가 상승할 것으로 예상되며, 글로벌 시장에서의 평가가 높아질 것으로 예상됩니다."},
            {"type": "digital_transformation", "headline": "{stock}의 디지털 전환 전략이 주가에 긍정적인 영향을 미칠 것으로 예상됩니다.", "details": "디지털 전환을 통한 {stock}의 효율성 증대가 주가 상승에 기여할 것으로 예상되며, 투자자들의 관심이 집중될 것으로 예상됩니다."},
            {"type": "innovation_automation", "headline": "{stock}의 자동화 기술 도입이 주가에 긍정적인 효과를 줄 것으로 예상됩니다.", "details": "자동화 기술 도입이 {stock}의 생산성과 효율성을 크게 향상시켜, 주가 상승에 긍정적으로 작용할 것으로 예상됩니다."},
            {"type": "corporate_responsibility", "headline": "{stock}의 사회적 책임 강화가 주가에 긍정적으로 작용할 것으로 예상됩니다.", "details": "사회적 책임 이행이 강화된 {stock}의 이미지 개선이 주가에 긍정적인 영향을 미칠 것으로 예상되며, 투자자들의 신뢰를 얻을 것으로 예상됩니다."},
            {"type": "merger_news", "headline": "{stock}의 합병 관련 소식이 시장에 긍정적으로 작용할 것으로 예상됩니다.", "details": "최근 발표된 합병 관련 소식이 {stock}의 기업 가치를 높일 것으로 예상되며, 주가 상승에 기여할 것으로 예상됩니다."},
            {"type": "market_trend", "headline": "현재 시장 트렌드가 {stock}의 주가에 영향을 미칠 것으로 예상됩니다.", "details": "시장 전반의 트렌드 변화가 {stock}의 주가에 반영될 것으로 예상되며, 투자자들은 이에 주목할 필요가 있습니다."},
            {"type": "technological_investment", "headline": "{stock}의 기술 투자 확대가 주가 상승을 이끌 것으로 예상됩니다.", "details": "신기술에 대한 투자 확대가 {stock}의 경쟁력 향상과 함께 주가 상승에 긍정적으로 작용할 것으로 예상됩니다."},
            {"type": "operational_efficiency", "headline": "{stock}의 운영 효율성 개선이 주가에 긍정적인 영향을 줄 것으로 예상됩니다.", "details": "효율적인 운영 전략이 {stock}의 비용 절감 및 수익성 개선으로 이어져, 주가 상승 기대감이 높아질 것으로 예상됩니다."},
            {"type": "brand_collaboration", "headline": "{stock}의 브랜드 콜라보레이션 소식이 주가에 긍정적인 영향을 줄 것으로 예상됩니다.", "details": "주요 브랜드와의 협업이 {stock}의 이미지와 시장 점유율 확대에 기여할 것으로 예상되며, 주가 상승 요인으로 작용할 것으로 예상됩니다."},
            {"type": "innovative_product", "headline": "{stock}의 혁신적인 신제품 출시가 주가에 긍정적인 영향을 줄 것으로 예상됩니다.", "details": "혁신적인 신제품 출시에 힘입어, {stock}의 주가가 상승할 것으로 예상되며, 시장의 관심이 집중될 것으로 예상됩니다."},
            {"type": "sustainability_initiative", "headline": "{stock}의 지속 가능한 경영 이니셔티브가 주가에 긍정적으로 작용할 것으로 예상됩니다.", "details": "환경 보호 및 지속 가능한 발전 전략이 {stock}의 기업 이미지 개선에 기여하여, 주가 상승에 긍정적인 영향을 미칠 것으로 예상됩니다."},
            {"type": "customer_growth", "headline": "{stock}의 고객 기반 확대가 주가에 긍정적인 영향을 줄 것으로 예상됩니다.", "details": "고객 기반이 확장됨에 따라 {stock}의 매출 및 주가가 상승할 것으로 예상되며, 투자자들의 관심이 증가할 것으로 예상됩니다."}
        ]

        # 생성할 뉴스 항목의 개수를 3~5개 사이로 결정 (종목이 부족하면 모두 사용)
        news_count = random.randint(3, 5)
        if len(stocks) < news_count:
            selected_stocks = stocks
        else:
            selected_stocks = random.sample(stocks, news_count)

        news_list = []
        for stock in selected_stocks:
            stock_name = stock.get("name", "알 수 없는 종목")
            template = random.choice(news_templates)
            headline = template["headline"].format(stock=stock_name)
            details = template["details"].format(stock=stock_name)
            news_list.append({"headline": headline, "details": details})
        
        self.current_news = news_list

    @commands.command(name="뉴스")
    async def news_command(self, ctx):
        """
        #뉴스: 최신 뉴스 항목들을 출력합니다.
        각 뉴스는 헤드라인과 상세 설명을 포함하여 실제 뉴스처럼 구성됩니다.
        """
        if not self.current_news:
            await ctx.send("현재 뉴스가 없습니다. 잠시 후 다시 시도해주세요.")
        else:
            message_lines = ["**최신 뉴스**"]
            for i, news in enumerate(self.current_news, start=1):
                message_lines.append(f"**[{i}] {news['headline']}**")
                message_lines.append(f"{news['details']}\n")
            news_message = "\n".join(message_lines)
            await ctx.send(news_message)

async def setup(bot):
    await bot.add_cog(StockNews(bot))
