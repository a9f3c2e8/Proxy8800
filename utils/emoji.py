"""Утилиты для работы с premium emoji в Telegram"""


class PremiumEmoji:
    """Класс для работы с premium emoji"""
    
    # Популярные premium emoji ID
    FIRE = "5368324170671202286"
    STAR = "5172632227871196306"
    ROCKET = "5368324170671202286"
    THUMBS_UP = "5368324170671202286"
    PARTY = "5368324170671202286"
    MONEY = "5368324170671202286"
    SHIELD = "5368324170671202286"
    CHECK = "5368324170671202286"
    SETTINGS = "4904936030232117798"  # ⚙️
    
    @staticmethod
    def format(emoji_char: str, emoji_id: str) -> str:
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
    
    @classmethod
    def fire(cls) -> str:
        """Возвращает огонь emoji"""
        return cls.format("🔥", cls.FIRE)
    
    @classmethod
    def star(cls) -> str:
        """Возвращает звезду emoji"""
        return cls.format("⭐", cls.STAR)
    
    @classmethod
    def rocket(cls) -> str:
        """Возвращает ракету emoji"""
        return cls.format("🚀", cls.ROCKET)
    
    @classmethod
    def thumbs_up(cls) -> str:
        """Возвращает палец вверх emoji"""
        return cls.format("👍", cls.THUMBS_UP)
    
    @classmethod
    def party(cls) -> str:
        """Возвращает праздник emoji"""
        return cls.format("🎉", cls.PARTY)
    
    @classmethod
    def money(cls) -> str:
        """Возвращает деньги emoji"""
        return cls.format("💰", cls.MONEY)
    
    @classmethod
    def shield(cls) -> str:
        """Возвращает щит emoji"""
        return cls.format("🛡", cls.SHIELD)
    
    @classmethod
    def check(cls) -> str:
        """Возвращает галочку emoji"""
        return cls.format("✅", cls.CHECK)
    
    @classmethod
    def settings(cls) -> str:
        """Возвращает настройки emoji"""
        return cls.format("⚙️", cls.SETTINGS)


# Удобные алиасы
emoji = PremiumEmoji()
