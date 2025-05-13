from config.girls import GIRLS

def calculate_girl_bonus(girl_id):
    """
    Возвращает бонусы от девушки.
    :param girl_id: ID девушки.
    :return: Словарь с бонусами к опыту и доходу.
    """
    if girl_id in GIRLS and GIRLS[girl_id]["bonus"]:
        # Возвращаем бонусы, гарантируя наличие ключей "experience" и "income"
        return {
            "experience": GIRLS[girl_id]["bonus"].get("experience", 0.0),
            "income": GIRLS[girl_id]["bonus"].get("income", 0.0)
        }
    return {"experience": 0.0, "income": 0.0}