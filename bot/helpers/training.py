RUNNING = 'Бег'
CYCLING = 'Велосипед'
STRENGTH = 'Силовая'
SWIMMING = 'Плавание'
CARDIO = 'Кардио'
WALKING = 'Ходьба'

calories_burned_in_hour = {
    RUNNING : 600,
    CYCLING: 500,
    STRENGTH: 400,
    SWIMMING: 700,
    CARDIO: 650,
    WALKING: 300
}

def count_training_waste(workout: str, minutes: int) -> tuple[int, int]:
    burned_calories = calories_burned_in_hour[workout] * minutes // 60
    burned_water = 200 * minutes // 30
    return burned_calories, burned_water