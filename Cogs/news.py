import os
import random
import discord
from discord.ext import commands, tasks
from datetime import datetime
import pytz
from pymongo import MongoClient

# 데이터베이스 설정
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
        DB의 상장된 주식 종목 중 무작위로 몇 종목을 선택하여,
        100개의 다양한 뉴스 템플릿 중 하나를 적용해 헤드라인과 상세 설명
        """
        stocks = list(self.db.stocks.find({"listed": True}))
        if not stocks:
            self.current_news = [{"headline": "현재 뉴스가 없습니다.", "details": ""}]
            return

        # 총 100개의 뉴스 템플릿 (4개 그룹으로 구성)
        news_templates = [
            {"type": "positive", "headline": "{stock}의 주가가 상승할 것으로 보입니다.", "details": "최근 투자자들의 긍정적 분위기와 거래량 증가로 인해, {stock}의 주가가 상승할 것으로 추정됩니다."},
            {"type": "negative", "headline": "{stock}의 주가가 급락할 것으로 추정됩니다.", "details": "최근 부정적인 이슈와 시장 불안으로 인해, {stock}의 주가가 급락할 가능성이 있습니다."},
            {"type": "neutral", "headline": "{stock} 관련 시장 동향에 변화가 감지됩니다.", "details": "시장 반응이 다양하게 나타나고 있어, {stock}의 주가에 대해 신중한 판단이 요구됩니다."},
            {"type": "in-depth_positive", "headline": "{stock}의 최신 분기 실적이 호조를 보일 것으로 예상됩니다.", "details": "{stock}의 실적이 예상치를 상회할 것으로 기대되며, 투자자들의 관심이 모아지고 있습니다."},
            {"type": "in-depth_negative", "headline": "{stock}의 경영진이 실적 부진에 대해 해명할 것으로 추정됩니다.", "details": "최근 {stock}의 실적 부진과 관련하여 경영진이 해명을 발표할 가능성이 있습니다."},
            {"type": "analysis", "headline": "전문가들은 {stock}의 단기 주가 변동이 불안정할 것으로 예측합니다.", "details": "시장 분석 결과, {stock}의 주가가 단기적으로 불안정하게 움직일 수 있음을 시사합니다."},
            {"type": "sentiment_negative", "headline": "투자 심리가 {stock}에 부정적으로 작용할 것으로 보입니다.", "details": "투자 심리 위축과 불안감으로 인해, {stock}의 주가 하락 우려가 제기되고 있습니다."},
            {"type": "sentiment_positive", "headline": "{stock}의 주가가 거래량 증가와 함께 상승할 것으로 추정됩니다.", "details": "거래량 증가가 긍정적인 신호로 작용하여, {stock}의 주가 상승 기대감이 있습니다."},
            {"type": "interest", "headline": "{stock}에 대한 투자자들의 관심이 확대될 것으로 보입니다.", "details": "시장 조사에 따르면, {stock}에 대한 관심이 높아지면서 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "product", "headline": "{stock}의 신제품 발표가 주가에 긍정적으로 작용할 것으로 보입니다.", "details": "다가오는 신제품 발표 소식에 힘입어, {stock}의 주가 상승 가능성이 있습니다."},
            {"type": "global", "headline": "{stock}의 글로벌 시장 진출이 주가를 견인할 것으로 보입니다.", "details": "글로벌 확장 전략이 {stock}의 주가에 긍정적인 영향을 미칠 것으로 기대됩니다."},
            {"type": "volatility", "headline": "최근 분석 결과, {stock}의 주가 변동성이 증가할 것으로 추정됩니다.", "details": "시장 전문가들은 {stock}의 주가가 단기적으로 큰 변동성을 보일 수 있음을 시사합니다."},
            {"type": "earnings", "headline": "{stock}의 실적 발표 후 주가에 변동이 있을 것으로 보입니다.", "details": "곧 발표될 {stock}의 실적에 따라 주가가 움직일 가능성이 있습니다."},
            {"type": "trade", "headline": "{stock}의 주가가 거래 호조에 힘입어 상승할 것으로 보입니다.", "details": "긍정적인 투자 분위기가 {stock}의 주가 상승에 기여할 것으로 기대됩니다."},
            {"type": "uncertainty", "headline": "시장 불안정 속에서 {stock}의 주가 하락 우려가 있습니다.", "details": "불안정한 경제 상황과 내부 이슈로 인해, {stock}의 주가 하락 가능성이 제기됩니다."},
            {"type": "innovation", "headline": "{stock}의 기술 혁신 소식이 주가에 긍정적으로 작용할 것으로 보입니다.", "details": "최근 기술 혁신 소식이 {stock}의 경쟁력을 강화하여 주가 상승에 기여할 것으로 기대됩니다."},
            {"type": "competition", "headline": "{stock}의 경쟁사 대비 분석 결과, 주가 조정 가능성이 있습니다.", "details": "경쟁사와의 비교에서 {stock}의 위치에 따라 주가 조정 가능성이 있습니다."},
            {"type": "strategy", "headline": "{stock}의 경영 전략 변화가 주가에 영향을 줄 수 있습니다.", "details": "최근 전략 변화가 {stock}의 주가에 영향을 미칠 가능성이 있으며, 시장의 반응이 주목됩니다."},
            {"type": "psychology", "headline": "투자자 심리 변화로 {stock}의 주가 조정 가능성이 있습니다.", "details": "심리 변화에 따라 {stock}의 주가가 일시적으로 조정될 가능성이 있습니다."},
            {"type": "investment", "headline": "{stock}의 신규 투자 소식이 주가 상승을 견인할 수 있습니다.", "details": "대규모 신규 투자가 {stock}의 주가에 긍정적인 영향을 미칠 가능성이 있습니다."},
            {"type": "stability", "headline": "{stock}의 주가가 안정적인 흐름을 유지할 가능성이 있습니다.", "details": "견고한 재무 구조가 {stock}의 주가 안정에 기여할 것으로 보입니다."},
            {"type": "issue", "headline": "최근 이슈로 인해 {stock}의 주가가 일시적으로 하락할 수 있습니다.", "details": "특정 이슈가 {stock}의 주가에 단기적인 영향을 미칠 가능성이 있습니다."},
            {"type": "overseas", "headline": "{stock}의 해외 진출 소식이 주가에 긍정적으로 작용할 수 있습니다.", "details": "해외 진출이 {stock}의 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "internal", "headline": "{stock}의 내부 이슈 해결 기대감이 주가에 긍정적으로 작용할 수 있습니다.", "details": "내부 이슈 해결이 {stock}의 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "adjustment", "headline": "전문가들은 {stock}의 주가가 단기 조정 국면에 들어갈 수 있다고 봅니다.", "details": "단기 조정 가능성이 있으나, 장기 성장 전망은 긍정적으로 평가됩니다."},
            {"type": "merger", "headline": "{stock}의 합병 소식이 시장에 큰 반향을 불러일으킬 수 있습니다.", "details": "최근 {stock} 관련 합병 소식이 투자자들의 관심을 모으며, 주가에 긍정적인 영향을 미칠 가능성이 있습니다."},
            {"type": "dividend", "headline": "{stock}의 배당 정책 변화가 주가에 영향을 줄 수 있습니다.", "details": "최근 발표된 배당 정책 변화가 {stock}의 주가에 긍정적인 신호를 줄 수 있습니다."},
            {"type": "regulation", "headline": "정부 규제 변화가 {stock}의 주가에 변동을 가져올 수 있습니다.", "details": "최근 정부 규제 변화가 {stock}의 주가에 영향을 미칠 가능성이 있으며, 주가 변동이 예상됩니다."},
            {"type": "scandal", "headline": "{stock} 관련 내부 스캔들이 주가에 부정적인 영향을 줄 수 있습니다.", "details": "내부 스캔들 소식이 {stock}의 주가 하락 우려를 불러일으킬 수 있습니다."},
            {"type": "innovation_tech", "headline": "{stock}의 AI 도입 소식이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "AI 기술 도입이 {stock}의 혁신을 이끌어내어 주가 상승 요인으로 작용할 수 있습니다."},
            {"type": "market_expansion", "headline": "{stock}의 해외 지사 확장이 주가 상승에 기여할 수 있습니다.", "details": "해외 지사 확장 계획이 {stock}의 글로벌 경쟁력을 강화하여 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "financial_results", "headline": "{stock}의 재무 지표 개선 소식이 주가에 긍정적으로 작용할 수 있습니다.", "details": "최근 {stock}의 재무 지표 개선이 투자자 신뢰를 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "supply_chain", "headline": "{stock}의 공급망 안정화 소식이 주가 상승에 기여할 수 있습니다.", "details": "공급망 문제 해결이 {stock}의 생산 효율성을 높여 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "research", "headline": "새로운 연구 결과가 {stock}의 성장 가능성을 높일 수 있습니다.", "details": "최근 연구 결과가 {stock}의 기술 및 시장 지위를 강화할 수 있음을 시사합니다."},
            {"type": "leadership", "headline": "{stock}의 경영진 교체 소식이 주가에 영향을 줄 수 있습니다.", "details": "경영진 교체 소식이 {stock}의 경영 전략에 변화를 가져와 주가 변동 가능성이 있습니다."},
            {"type": "market_sentiment", "headline": "시장 전반의 긍정적인 분위기가 {stock}의 주가 상승을 견인할 수 있습니다.", "details": "긍정적인 시장 심리가 {stock}의 주가에 긍정적으로 작용할 가능성이 있습니다."},
            {"type": "partnership", "headline": "{stock}의 전략적 제휴 소식이 주가에 긍정적인 모멘텀을 제공할 수 있습니다.", "details": "최근 {stock}과 주요 기업 간의 제휴가 체결되어 주가 상승 기대감이 형성될 수 있습니다."},
            {"type": "merger_2", "headline": "{stock}의 인수합병 움직임이 시장에 큰 파장을 일으킬 수 있습니다.", "details": "최근 {stock} 관련 인수합병 소식이 주가 변동성을 높일 가능성이 있습니다."},
            {"type": "economic", "headline": "글로벌 경제 상황 변화가 {stock}의 주가에 영향을 줄 수 있습니다.", "details": "최근 경제 지표 변화가 {stock}의 산업 환경에 영향을 미쳐 주가 변동을 야기할 수 있습니다."},
            {"type": "innovation_fintech", "headline": "{stock}의 핀테크 혁신이 금융 시장에 긍정적으로 작용할 수 있습니다.", "details": "최신 핀테크 솔루션 도입이 {stock}의 효율성을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "customer", "headline": "{stock}의 고객 서비스 개선이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "최근 고객 만족도 향상 정책이 {stock}의 투자자 신뢰를 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_research", "headline": "{stock}의 연구개발 투자 확대가 장기 성장에 기여할 수 있습니다.", "details": "연구개발 투자 확대가 {stock}의 경쟁력 강화를 통해 주가 상승에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "stock_split", "headline": "{stock}의 주식 분할 계획이 투자자들에게 긍정적으로 작용할 수 있습니다.", "details": "주식 분할 계획 발표가 {stock}의 접근성을 높여 주가 상승 요인으로 작용할 수 있습니다."},
            {"type": "insider_trading", "headline": "{stock} 내부자의 거래 소식이 주가에 단기적인 영향을 줄 수 있습니다.", "details": "최근 {stock} 내부자 거래 소식이 단기 주가 변동을 야기할 수 있으나, 장기 영향은 미미할 수 있습니다."},
            {"type": "seasonal", "headline": "계절적 요인에 따라 {stock}의 주가가 조정될 수 있습니다.", "details": "계절적 수요 변화가 {stock}의 주가에 일시적인 조정을 가져올 수 있습니다."},
            {"type": "tech", "headline": "{stock}의 AI 도입 소식이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "최근 AI 기술 도입이 {stock}의 혁신을 이끌어내어 주가 상승 요인으로 작용할 가능성이 있습니다."},
            {"type": "sustainability", "headline": "{stock}의 친환경 경영 전략이 주가에 긍정적인 효과를 줄 수 있습니다.", "details": "환경 친화적 정책이 {stock}의 브랜드 이미지를 강화하여 주가에 긍정적인 영향을 미칠 수 있습니다."},
            {"type": "expansion", "headline": "{stock}의 해외 지사 확장이 주가 상승을 견인할 수 있습니다.", "details": "해외 지사 확장 계획이 {stock}의 글로벌 경쟁력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_biotech", "headline": "{stock}의 바이오 기술 혁신이 투자자들의 기대를 모을 수 있습니다.", "details": "최신 바이오 기술 및 연구 성과가 {stock}의 성장 동력으로 작용하여 주가 상승에 기여할 수 있습니다."},
            {"type": "expensive", "headline": "{stock}의 고가 정책이 시장에서 논란을 불러일으킬 수 있습니다.", "details": "고가 전략이 {stock}의 매출에 영향을 미쳐 주가 변동성이 증가할 수 있다는 우려가 있습니다."},
            {"type": "partnership_2", "headline": "{stock}과(와) 주요 기업 간의 제휴가 주가 상승에 기여할 수 있습니다.", "details": "최근 {stock}과 주요 기업 간의 전략적 제휴가 체결되어 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "market_demand", "headline": "{stock}의 제품 수요 증가가 주가 상승을 부추길 수 있습니다.", "details": "시장 내 {stock} 제품 수요 증가가 주가 상승 요인으로 작용할 수 있습니다."},
            {"type": "trade_volume", "headline": "{stock}의 거래량 증가가 주가에 긍정적인 모멘텀을 제공할 수 있습니다.", "details": "거래량 급증이 {stock}의 주가 상승에 기여할 수 있는 모멘텀을 형성할 수 있습니다."},
            {"type": "innovation_retail", "headline": "{stock}의 소매 혁신 전략이 주가 상승에 기여할 수 있습니다.", "details": "혁신적인 소매 전략이 {stock}의 경쟁력을 높여 주가 상승에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "brand_value", "headline": "{stock}의 브랜드 가치 상승이 주가에 반영될 수 있습니다.", "details": "강력한 브랜드 인지도와 가치 상승이 {stock}의 주가에 긍정적인 영향을 미칠 수 있습니다."},
            {"type": "corporate_governance", "headline": "{stock}의 기업 거버넌스 개선이 주가에 긍정적으로 작용할 수 있습니다.", "details": "투명한 경영 체제와 개선된 거버넌스가 {stock}의 투자자 신뢰를 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "risky", "headline": "{stock}의 공격적인 사업 전략이 단기적으로 주가 변동을 초래할 수 있습니다.", "details": "공격적인 사업 확장 전략이 {stock}의 주가에 단기적인 불확실성을 야기할 수 있습니다."},
            {"type": "supply_demand", "headline": "{stock}의 공급과 수요 불균형이 주가에 변동을 줄 수 있습니다.", "details": "공급 부족과 수요 증가가 동시에 발생할 경우, {stock}의 주가에 단기적인 변동이 있을 수 있습니다."},
            {"type": "new_contract", "headline": "{stock}의 신규 계약 체결 소식이 주가에 긍정적인 모멘텀을 제공할 수 있습니다.", "details": "최근 {stock}의 신규 계약 체결 소식이 주가 상승 기대감을 불러일으킬 수 있습니다."},
            {"type": "cost_cutting", "headline": "{stock}의 비용 절감 정책이 주가에 긍정적으로 작용할 수 있습니다.", "details": "효율적인 비용 절감 전략이 {stock}의 수익성을 개선하여 주가 상승에 기여할 수 있습니다."},
            {"type": "market_share", "headline": "{stock}의 시장 점유율 확대가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "시장 점유율 확대가 {stock}의 경쟁력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_ecommerce", "headline": "{stock}의 전자상거래 혁신이 주가 상승에 기여할 수 있습니다.", "details": "전자상거래 분야의 혁신 전략이 {stock}의 매출 증대로 이어져 주가 상승에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "economic_policy", "headline": "정부의 경제 정책 변화가 {stock}의 주가에 영향을 줄 수 있습니다.", "details": "최근 경제 정책 변화가 {stock}의 산업 환경에 긍정적인 영향을 미쳐 주가 변동에 기여할 수 있습니다."},
            {"type": "foreign_investment", "headline": "{stock}에 대한 해외 투자자들의 관심이 주가에 긍정적으로 작용할 수 있습니다.", "details": "해외 투자자들의 관심이 증가하면서 {stock}의 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "digital_transformation", "headline": "{stock}의 디지털 전환 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "디지털 전환을 통한 {stock}의 효율성 증대가 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_automation", "headline": "{stock}의 자동화 기술 도입이 주가에 긍정적인 효과를 줄 수 있습니다.", "details": "자동화 기술 도입이 {stock}의 생산성과 효율성을 크게 향상시켜 주가 상승에 기여할 수 있습니다."},
            {"type": "corporate_responsibility", "headline": "{stock}의 사회적 책임 강화가 주가에 긍정적으로 작용할 수 있습니다.", "details": "사회적 책임 이행 강화가 {stock}의 이미지 개선에 기여하여 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "merger_news", "headline": "{stock}의 합병 관련 소식이 주가에 긍정적으로 작용할 수 있습니다.", "details": "최근 합병 관련 소식이 {stock}의 기업 가치를 높여 주가 상승 요인으로 작용할 수 있습니다."},
            {"type": "market_trend", "headline": "현재 시장 트렌드가 {stock}의 주가에 빠르게 반영될 수 있습니다.", "details": "시장 전반의 트렌드 변화가 {stock}의 주가에 즉각적인 영향을 줄 수 있습니다."},
            {"type": "technological_investment", "headline": "{stock}의 기술 투자 확대가 주가 상승을 견인할 수 있습니다.", "details": "신기술 투자 확대가 {stock}의 경쟁력 강화를 통해 주가 상승에 기여할 수 있습니다."},
            {"type": "operational_efficiency", "headline": "{stock}의 운영 효율성 개선이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효율적인 운영 전략이 {stock}의 비용 절감 및 수익성 개선으로 이어져 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "brand_collaboration", "headline": "{stock}의 브랜드 콜라보레이션 소식이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "주요 브랜드와의 협업이 {stock}의 이미지와 시장 점유율 확대에 기여하여 주가 상승 요인으로 작용할 수 있습니다."},
            {"type": "innovative_product", "headline": "{stock}의 혁신적인 신제품 출시가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "혁신적인 신제품 출시에 힘입어 {stock}의 주가가 상승할 가능성이 있습니다."},
            {"type": "sustainability_initiative", "headline": "{stock}의 지속 가능한 경영 이니셔티브가 주가에 긍정적으로 작용할 수 있습니다.", "details": "지속 가능한 경영 전략이 {stock}의 이미지 개선에 기여하여 주가 상승에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "customer_growth", "headline": "{stock}의 고객 기반 확대가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "고객 기반 확대로 인해 {stock}의 매출 및 주가가 상승할 가능성이 있습니다."},
            {"type": "market_overview", "headline": "최근 시장 동향이 {stock}의 주가에 긍정적인 영향을 미칠 수 있습니다.", "details": "시장 전반의 흐름이 {stock}의 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "investment_forecast", "headline": "분석가들은 {stock}의 주가가 상승할 것으로 전망합니다.", "details": "최근 분석 결과에 따르면, {stock}의 주가 상승 가능성이 크다고 예측됩니다."},
            {"type": "economic_growth", "headline": "긍정적인 경제 성장 전망이 {stock}의 주가에 반영될 수 있습니다.", "details": "경제 성장세가 {stock}의 사업 환경 개선에 기여하여 주가 상승에 영향을 줄 수 있습니다."},
            {"type": "sector_trend", "headline": "해당 섹터의 성장 추세가 {stock}의 주가에 긍정적으로 작용할 수 있습니다.", "details": "산업 섹터 내 성장 추세가 {stock}의 주가 상승 모멘텀으로 이어질 수 있습니다."},
            {"type": "strategic_move", "headline": "{stock}의 전략적 움직임이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "최근 {stock}의 전략적 변화가 주가 상승 요인으로 작용할 가능성이 있습니다."},
            {"type": "regulatory_support", "headline": "정부의 규제 지원 정책이 {stock}의 주가 상승에 기여할 수 있습니다.", "details": "정부의 지원 정책이 {stock}의 산업 환경 개선에 도움을 주어 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "tech_innovation", "headline": "{stock}의 기술 혁신이 주가 상승 모멘텀을 강화할 수 있습니다.", "details": "첨단 기술 혁신이 {stock}의 경쟁력 강화를 이끌어 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "market_signal", "headline": "시장 신호가 {stock}의 주가에 즉각적으로 반영될 수 있습니다.", "details": "최근 발표된 시장 신호가 {stock}의 주가에 빠르게 영향을 줄 수 있습니다."},
            {"type": "growth_potential", "headline": "{stock}의 성장 잠재력이 주가에 긍정적으로 작용할 수 있습니다.", "details": "강력한 성장 잠재력이 {stock}의 주가 상승을 견인할 가능성이 있습니다."},
            {"type": "customer_loyalty", "headline": "{stock}의 고객 충성도가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "높은 고객 충성도가 {stock}의 매출 증대로 이어져 주가 상승에 기여할 수 있습니다."},
            {"type": "supply_stability", "headline": "{stock}의 안정적인 공급망이 주가에 긍정적으로 작용할 수 있습니다.", "details": "안정적인 공급망 관리가 {stock}의 생산 효율성을 높여 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "innovation_strategy", "headline": "{stock}의 혁신 전략이 주가 상승을 이끌 수 있습니다.", "details": "혁신 전략이 {stock}의 경쟁력을 강화하여 주가 상승 모멘텀으로 작용할 가능성이 있습니다."},
            {"type": "market_adaptation", "headline": "{stock}이 변화하는 시장에 빠르게 적응할 것으로 보입니다.", "details": "{stock}의 시장 적응 능력이 주가 안정 및 상승에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "operational_improvement", "headline": "{stock}의 운영 개선이 주가에 긍정적으로 반영될 수 있습니다.", "details": "운영 효율성 증대가 {stock}의 수익 개선으로 이어져 주가에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "investor_confidence", "headline": "투자자 신뢰가 {stock}의 주가 상승을 지원할 수 있습니다.", "details": "투자자들의 신뢰도가 {stock}의 주가에 긍정적으로 작용할 가능성이 있습니다."},
            {"type": "future_prospects", "headline": "{stock}의 미래 전망이 주가에 긍정적으로 반영될 수 있습니다.", "details": "장기적인 성장 전망이 {stock}의 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "sector_performance", "headline": "해당 섹터의 좋은 실적이 {stock}의 주가에 긍정적으로 작용할 수 있습니다.", "details": "섹터 전반의 좋은 실적이 {stock}의 주가 상승 모멘텀으로 이어질 수 있습니다."},
            {"type": "strategic_initiative", "headline": "{stock}의 새로운 전략적 이니셔티브가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 전략이 {stock}의 경쟁력을 강화하여 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "external_factors", "headline": "외부 요인이 {stock}의 주가에 빠르게 반영될 수 있습니다.", "details": "외부 경제 및 정치 요인이 {stock}의 주가에 영향을 미쳐 단기 변동성이 발생할 수 있습니다."},
            {"type": "revenue_growth", "headline": "{stock}의 매출 성장률이 주가에 긍정적인 신호로 작용할 수 있습니다.", "details": "높은 매출 성장률이 {stock}의 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "profitability", "headline": "{stock}의 수익성 개선이 주가에 긍정적으로 반영될 수 있습니다.", "details": "수익성 개선이 {stock}의 주가에 긍정적인 영향을 미쳐 상승 모멘텀을 강화할 수 있습니다."},
            {"type": "market_rebound", "headline": "과거 주가 하락 이후 {stock}의 주가가 반등할 수 있습니다.", "details": "과거 조정 이후 {stock}의 주가가 반등할 가능성이 있으며, 투자자들이 이에 주목할 수 있습니다."},
            {"type": "tech_leadership", "headline": "{stock}의 기술 리더십이 주가 상승을 견인할 수 있습니다.", "details": "강력한 기술 리더십이 {stock}의 경쟁력 강화에 기여하여 주가 상승에 긍정적으로 작용할 수 있습니다."},
            {"type": "innovation_pipeline", "headline": "{stock}의 혁신적인 제품 파이프라인이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "혁신적인 제품 개발 계획이 {stock}의 장기 성장에 기여하여 주가 상승을 이끌 수 있습니다."},
            {"type": "sector_growth", "headline": "해당 산업 섹터의 성장 전망이 {stock}의 주가에 긍정적으로 반영될 수 있습니다.", "details": "산업 섹터 내 성장 전망이 {stock}의 주가 상승에 기여할 가능성이 있습니다."}
            {"type": "eco_trend", "headline": "{stock}의 친환경 트렌드가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "최근 친환경 정책과 소비자 선호도가 {stock}의 사업에 긍정적인 영향을 미쳐 주가 상승 가능성이 있습니다."},
            {"type": "tech_investment", "headline": "{stock}의 기술 투자 확대가 주가 상승 모멘텀을 강화할 수 있습니다.", "details": "첨단 기술 투자로 인해 {stock}의 경쟁력이 강화되어 주가에 긍정적인 영향을 미칠 가능성이 있습니다."},
            {"type": "supply_chain_optimization", "headline": "{stock}의 공급망 최적화가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효율적인 공급망 관리가 {stock}의 생산성을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "market_expansion_strategy", "headline": "{stock}의 시장 확장 전략이 주가에 긍정적으로 작용할 수 있습니다.", "details": "새로운 시장 개척이 {stock}의 매출 증대로 이어져 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "product_innovation", "headline": "{stock}의 제품 혁신이 주가 상승을 견인할 수 있습니다.", "details": "혁신적인 제품 개발이 {stock}의 경쟁력을 강화하여 주가 상승에 긍정적인 영향을 미칠 수 있습니다."},
            {"type": "customer_experience", "headline": "{stock}의 고객 경험 개선이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "고객 만족도 향상이 {stock}의 브랜드 가치 상승에 기여하여 주가 상승 모멘텀을 강화할 수 있습니다."},
            {"type": "digital_marketing", "headline": "{stock}의 디지털 마케팅 강화가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "디지털 채널을 통한 마케팅 전략이 {stock}의 인지도와 매출 증대로 이어져 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_collaboration", "headline": "{stock}의 혁신 협업 소식이 주가에 긍정적인 모멘텀을 제공할 수 있습니다.", "details": "다양한 기업과의 협업이 {stock}의 기술력과 시장 경쟁력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "brand_recognition", "headline": "{stock}의 브랜드 인지도 상승이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "높은 브랜드 인지도가 {stock}의 시장 점유율 확대와 주가 상승에 기여할 수 있습니다."},
            {"type": "financial_innovation", "headline": "{stock}의 금융 혁신 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 금융 상품 및 서비스 도입이 {stock}의 수익성을 개선하여 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "operational_cost_reduction", "headline": "{stock}의 운영 비용 절감이 주가에 긍정적인 영향을 미칠 수 있습니다.", "details": "효율적인 비용 관리 전략이 {stock}의 이익 개선에 기여하여 주가 상승에 긍정적인 효과를 줄 수 있습니다."},
            {"type": "expansion_into_new_segments", "headline": "{stock}의 신시장 진출이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 고객층 확보와 시장 다각화가 {stock}의 매출 증대로 이어져 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "sustainability_investment", "headline": "{stock}의 지속 가능한 투자 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "지속 가능한 경영과 투자 전략이 {stock}의 장기 성장에 기여할 가능성이 있습니다."},
            {"type": "data_driven_strategy", "headline": "{stock}의 데이터 기반 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "빅데이터와 인공지능을 활용한 전략이 {stock}의 운영 효율성을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "market_restructuring", "headline": "{stock}의 시장 구조 재편이 주가에 긍정적으로 작용할 수 있습니다.", "details": "산업 내 재편이 {stock}의 경쟁 환경을 개선하여 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "innovative_supply_chain", "headline": "{stock}의 혁신적인 공급망 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 공급망 전략이 {stock}의 생산성과 효율성을 높여 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "market_rationalization", "headline": "{stock}의 시장 합리화 움직임이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "시장 내 불필요한 경쟁 요소 제거가 {stock}의 주가에 긍정적인 영향을 미칠 수 있습니다."},
            {"type": "innovative_financial_products", "headline": "{stock}의 혁신적인 금융 상품 출시가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 금융 상품이 {stock}의 매출과 수익성을 개선하여 주가 상승에 기여할 수 있습니다."},
            {"type": "risk_management", "headline": "{stock}의 리스크 관리 강화가 주가에 긍정적으로 작용할 수 있습니다.", "details": "효과적인 리스크 관리가 {stock}의 안정적인 성과에 기여하여 주가 상승에 긍정적인 영향을 미칠 수 있습니다."},
            {"type": "sustainable_growth", "headline": "{stock}의 지속 가능한 성장 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "지속 가능한 성장 전략이 {stock}의 장기적인 경쟁력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_in_customer_service", "headline": "{stock}의 고객 서비스 혁신이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "고객 서비스 개선이 {stock}의 고객 만족도와 브랜드 충성도를 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "technology_integration", "headline": "{stock}의 최신 기술 통합이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "최신 기술의 통합이 {stock}의 운영 효율성을 향상시켜 주가 상승에 기여할 수 있습니다."},
            {"type": "merger_strategy", "headline": "{stock}의 합병 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효과적인 합병 전략이 {stock}의 시장 지배력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_in_marketing", "headline": "{stock}의 마케팅 혁신이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "창의적인 마케팅 전략이 {stock}의 브랜드 가치를 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "global_partnership", "headline": "{stock}의 글로벌 파트너십이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "글로벌 기업과의 협력이 {stock}의 해외 시장 확장에 기여하여 주가 상승 모멘텀을 강화할 수 있습니다."},
            {"type": "strategic_investment", "headline": "{stock}의 전략적 투자 유치가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "유명 투자자로부터의 투자 유치가 {stock}의 성장 가능성을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "profit_margin", "headline": "{stock}의 이익률 개선이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "높은 이익률이 {stock}의 재무 건전성을 개선하여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_in_distribution", "headline": "{stock}의 유통 혁신이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효율적인 유통 시스템이 {stock}의 매출 증대로 이어져 주가 상승에 기여할 수 있습니다."},
            {"type": "market_leadership", "headline": "{stock}의 시장 리더십이 주가 상승을 견인할 수 있습니다.", "details": "강력한 시장 리더십이 {stock}의 주가 상승 모멘텀을 강화할 수 있습니다."},
            {"type": "strategic_diversification", "headline": "{stock}의 전략적 다각화가 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "사업 영역 다각화가 {stock}의 성장 잠재력을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "competitive_pricing", "headline": "{stock}의 경쟁력 있는 가격 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "가격 경쟁력이 {stock}의 시장 점유율 확대에 기여하여 주가 상승에 긍정적인 효과를 줄 수 있습니다."},
            {"type": "cost_efficiency_strategy", "headline": "{stock}의 비용 효율성 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효율적인 비용 관리가 {stock}의 이익 개선으로 이어져 주가 상승에 기여할 수 있습니다."},
            {"type": "sustainability_reporting", "headline": "{stock}의 지속 가능성 보고가 투자자 신뢰를 높여 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "투명한 지속 가능성 보고가 {stock}의 기업 가치를 향상시켜 주가 상승에 기여할 수 있습니다."},
            {"type": "innovative_business_model", "headline": "{stock}의 혁신적인 비즈니스 모델이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 비즈니스 모델 도입이 {stock}의 시장 경쟁력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "eco_trend_2", "headline": "{stock}의 친환경 제품 라인이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "친환경 제품 수요 증가가 {stock}의 매출과 주가에 긍정적인 효과를 줄 수 있습니다."},
            {"type": "tech_trend", "headline": "{stock}의 최신 기술 트렌드가 주가 상승을 이끌 수 있습니다.", "details": "최신 기술 도입이 {stock}의 경쟁력을 강화하여 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "market_innovation", "headline": "{stock}의 혁신적인 시장 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "새로운 시장 전략이 {stock}의 매출 증대에 기여하여 주가 상승에 영향을 미칠 수 있습니다."},
            {"type": "consumer_behavior", "headline": "{stock}의 소비자 행동 변화가 주가에 반영될 수 있습니다.", "details": "소비자 선호도 변화가 {stock}의 제품 판매에 긍정적인 영향을 줄 수 있습니다."},
            {"type": "financial_health", "headline": "{stock}의 재무 건전성이 주가에 긍정적으로 작용할 수 있습니다.", "details": "안정적인 재무 상태가 {stock}의 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_leadership", "headline": "{stock}의 혁신 리더십이 주가 상승 모멘텀을 강화할 수 있습니다.", "details": "혁신적인 경영진이 {stock}의 성장을 견인하여 주가 상승에 기여할 가능성이 있습니다."},
            {"type": "cost_structure", "headline": "{stock}의 비용 구조 개선이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효율적인 비용 구조 개선이 {stock}의 이익률을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "market_dynamics", "headline": "시장 역학 변화가 {stock}의 주가에 반영될 수 있습니다.", "details": "시장 내 역학 변화가 {stock}의 주가 변동에 영향을 줄 수 있습니다."},
            {"type": "customer_satisfaction", "headline": "{stock}의 고객 만족도가 주가에 긍정적으로 작용할 수 있습니다.", "details": "높은 고객 만족도가 {stock}의 브랜드 가치를 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "strategic_planning", "headline": "{stock}의 전략적 계획이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "장기 전략이 {stock}의 성장 전망에 긍정적인 신호를 줄 수 있습니다."},
            {"type": "global_expansion_plan", "headline": "{stock}의 글로벌 확장 계획이 주가에 반영될 수 있습니다.", "details": "해외 시장 진출이 {stock}의 매출 증대와 주가 상승에 기여할 수 있습니다."},
            {"type": "technology_adoption", "headline": "{stock}의 신기술 채택이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "신기술 도입이 {stock}의 효율성과 경쟁력을 강화하여 주가 상승에 기여할 수 있습니다."},
            {"type": "innovation_integration", "headline": "{stock}의 혁신 통합 전략이 주가에 긍정적으로 작용할 수 있습니다.", "details": "다양한 혁신 전략이 {stock}의 시장 경쟁력을 높여 주가 상승에 기여할 수 있습니다."},
            {"type": "customer_retention", "headline": "{stock}의 고객 유지 전략이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "효과적인 고객 유지 정책이 {stock}의 안정적인 매출에 기여하여 주가 상승에 긍정적인 효과를 줄 수 있습니다."},
            {"type": "market_volatility_control", "headline": "{stock}의 변동성 관리 전략이 주가에 긍정적으로 작용할 수 있습니다.", "details": "효과적인 변동성 관리가 {stock}의 주가 안정에 기여할 수 있습니다."},
            {"type": "innovation_forecasting", "headline": "{stock}의 혁신 예측이 주가에 긍정적인 영향을 줄 수 있습니다.", "details": "미래 혁신 전략이 {stock}의 성장 가능성을 높여 주가 상승에 기여할 수 있습니다."}
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

        # 뉴스 데이터를 DB에 저장 (컬렉션 이름: "news")
        now = datetime.now(pytz.timezone("Asia/Seoul"))
        news_doc = {
            "timestamp": now,
            "news": news_list
        }
        self.db.news.insert_one(news_doc)

    @commands.command(name="뉴스")
    async def news_command(self, ctx):
        """
        #뉴스: 최신 뉴스 항목들을 Embed 형태로 출력합니다.
        """
        # DB에서 가장 최신 뉴스 문서를 조회합니다.
        latest_news = self.db.news.find_one(sort=[("timestamp", -1)])
        if not latest_news or not latest_news.get("news"):
            await ctx.send("현재 뉴스가 없습니다. 잠시 후 다시 시도해주세요.")
        else:
            news_list = latest_news["news"]
            now = datetime.now(pytz.timezone("Asia/Seoul"))
            embed = discord.Embed(
                title="📰 최신 뉴스",
                description="아래는 최신으로 저장된 뉴스 항목입니다.",
                color=discord.Color.gold(),
                timestamp=now
            )
            for i, news in enumerate(news_list, start=1):
                embed.add_field(
                    name=f"뉴스 {i}: {news['headline']}",
                    value=news['details'],
                    inline=False
                )
            embed.set_footer(text="주식 뉴스 업데이트")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StockNews(bot))
