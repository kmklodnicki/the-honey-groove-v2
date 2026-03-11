"""Smart Rarity Engine — BLOCK 446"""


def calculate_rarity(community_have: int, community_want: int) -> str:
    """Calculate rarity label from Discogs community have/want data.

    Thresholds:
      Grail (Purple/Gold): ratio > 20 AND have < 500
      Ultra Rare (Orange): ratio 8-20
      Rare (Red): ratio 3-8
      Uncommon (Blue): ratio 1-3
      Common (Gray): ratio < 1

    Obscure exception: have < 25 AND want < 10 → 'Obscure'
    """
    have = max(community_have or 0, 1)  # avoid division by zero
    want = community_want or 0

    # Obscure exception first
    if have < 25 and want < 10:
        return "Obscure"

    ratio = want / have

    if ratio > 20 and have < 500:
        return "Grail"
    elif ratio > 20:
        return "Ultra Rare"
    elif ratio >= 8:
        return "Ultra Rare"
    elif ratio >= 3:
        return "Rare"
    elif ratio >= 1:
        return "Uncommon"
    else:
        return "Common"
