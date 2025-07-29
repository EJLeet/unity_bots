from bot.config.config import Config

class RankData:
    # Rank hierarchy (order matters)
    RANK_HIERARCHY = [
        'Mediator',
        'Sage', 
        'Destroyer',
        'Unholy',
        'Legend'
    ]
    
    # Promotion thresholds (career counter based)
    PROMOTION_THRESHOLDS = {
        'Sage': Config.SAGE_PROMOTION_THRESHOLD,
        'Destroyer': Config.DESTROYER_PROMOTION_THRESHOLD, 
        'Unholy': Config.UNHOLY_PROMOTION_THRESHOLD,
    }
    
    # Time-based promotion requirements
    TIME_REQUIREMENTS = {
        'Mediator': Config.MEDIATOR_TIME_REQUIREMENT_DAYS
    }
    
    # Role ID mapping
    ROLE_IDS = Config.ROLE_MAPPING
    
    @classmethod
    def get_next_rank(cls, current_rank: str) -> str:
        try:
            current_index = cls.RANK_HIERARCHY.index(current_rank)
            if current_index < len(cls.RANK_HIERARCHY) - 1:
                return cls.RANK_HIERARCHY[current_index + 1]
            return None  # Already at max rank
        except ValueError:
            return None  # Invalid current rank
    
    @classmethod
    def get_rank_role_id(cls, rank: str) -> int:
        return cls.ROLE_IDS.get(rank, 0)
    
    @classmethod
    def is_promotable_rank(cls, rank: str) -> bool:
        # Legend is not promotable (max rank)
        return rank in cls.RANK_HIERARCHY[:-1]
    
    @classmethod
    def get_promotion_threshold(cls, target_rank: str) -> int:
        return cls.PROMOTION_THRESHOLDS.get(target_rank, 0)
    
    @classmethod
    def is_time_based_promotion(cls, current_rank: str) -> bool:
        return current_rank in cls.TIME_REQUIREMENTS
    
    @classmethod
    def get_time_requirement(cls, rank: str) -> int:
        return cls.TIME_REQUIREMENTS.get(rank, 0)