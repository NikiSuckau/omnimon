import core.constants as constants
from core import runtime_globals


ALERT_DURATION_FRAMES = int(50 * (constants.FRAME_RATE / 30))
WAIT_AFTER_BAR_FRAMES = int(30 * (constants.FRAME_RATE / 30))
IMPACT_DURATION_FRAMES = int(60 * (constants.FRAME_RATE / 30))
WAIT_ATTACK_READY_FRAMES = int(20 * (constants.FRAME_RATE / 30))
RESULT_SCREEN_FRAMES = int(90 * (constants.FRAME_RATE / 30))
BAR_HOLD_TIME_MS = 2500
PUNCH_HOLD_TIME_MS = 18000
ATTACK_SPEED = 4 * (runtime_globals.SCREEN_WIDTH / 240)

ENEMY_ENTRY_SPEED = 1 * (runtime_globals.SCREEN_WIDTH / 240)
IDLE_ANIM_DURATION = int(90 * (constants.FRAME_RATE / 30))
ALERT_FRAME_DELAY = int(10 * (constants.FRAME_RATE / 30))
AFTER_ATTACK_DELAY_FRAMES = int(50 * (constants.FRAME_RATE / 30))
LEVEL_DURATION_FRAMES = int(60 * (constants.FRAME_RATE / 30))

READY_FRAME_COUNTER = int(60 * (constants.FRAME_RATE / 30))
ALERT_FRAME_COUNTER = int(90 * (constants.FRAME_RATE / 30))

def update_combat_constants():
    global ALERT_DURATION_FRAMES, WAIT_AFTER_BAR_FRAMES, IMPACT_DURATION_FRAMES, WAIT_ATTACK_READY_FRAMES
    global RESULT_SCREEN_FRAMES, ATTACK_SPEED, ENEMY_ENTRY_SPEED, IDLE_ANIM_DURATION
    global ALERT_FRAME_DELAY, AFTER_ATTACK_DELAY_FRAMES, LEVEL_DURATION_FRAMES
    global READY_FRAME_COUNTER, ALERT_FRAME_COUNTER

    ALERT_DURATION_FRAMES = int(60 * (constants.FRAME_RATE / 30))
    WAIT_AFTER_BAR_FRAMES = int(30 * (constants.FRAME_RATE / 30))
    IMPACT_DURATION_FRAMES = int(60 * (constants.FRAME_RATE / 30))
    WAIT_ATTACK_READY_FRAMES = int(20 * (constants.FRAME_RATE / 30))
    RESULT_SCREEN_FRAMES = int(90 * (constants.FRAME_RATE / 30))
    ATTACK_SPEED = 4 * (runtime_globals.SCREEN_WIDTH / 240)
    ENEMY_ENTRY_SPEED = 1 * (runtime_globals.SCREEN_WIDTH / 240)
    IDLE_ANIM_DURATION = int(90 * (constants.FRAME_RATE / 30))
    ALERT_FRAME_DELAY = int(10 * (constants.FRAME_RATE / 30))
    AFTER_ATTACK_DELAY_FRAMES = int(50 * (constants.FRAME_RATE / 30))
    LEVEL_DURATION_FRAMES = int(60 * (constants.FRAME_RATE / 30))
    READY_FRAME_COUNTER = int(60 * (constants.FRAME_RATE / 30))
    ALERT_FRAME_COUNTER = int(90 * (constants.FRAME_RATE / 30))


# Usage elsewhere:
# speed = get_attack_speed()
# entry_speed = get_enemy_entry_speed()