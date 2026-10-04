from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


# =========================================================
# WINDOW SETUP
# =========================================================
Window.clearcolor = (0.96, 0.97, 0.99, 1)  # Soft premium background color like the image


# =========================================================
# PREDICTION LOGIC (All Confirmed Rule Updates)
# =========================================================

def get_big_small(num):
    return "Big" if num >= 5 else "Small"


def predict_pattern_1(history):
    if len(history) < 4:
        return "No Prediction"
    p1 = history[-4]
    p3 = history[-2]
    # Existing Rule 1 condition: equal 1st and 3rd numbers -> No Prediction.
    if p1 == p3:
        return "No Prediction"
    steps = (p3 - p1) % 10
    predicted = (p3 + steps) % 10
    return get_big_small(predicted)


def predict_pattern_2(history, period_counts):
    if len(history) < 2:
        return "No Prediction"
    last_num = history[-1]
    current_idx = len(history) - 1
    current_period_parity = period_counts[current_idx] % 2
    lookback = min(20, len(history) - 1)

    for i in range(2, lookback + 1):
        idx = len(history) - i
        if period_counts[idx] % 2 == current_period_parity:
            if history[idx] == last_num:
                if idx + 1 < len(history):
                    return get_big_small(history[idx + 1])
    return "No Prediction"


def predict_pattern_3(history):
    # Main numbers for Pattern 3
    main_numbers = {6, 3, 1, 8}

    if not history:
        return "No Prediction"

    # If a pair of consecutive periods are both main numbers,
    # the next two predictions are No Prediction. This applies
    # regardless of what numbers appear in those next periods.
    for i in range(len(history) - 2, -1, -1):
        if history[i] in main_numbers and history[i + 1] in main_numbers:
            periods_after_pair = (len(history) - 1) - (i + 1)
            if periods_after_pair in (0, 1):
                return "No Prediction"
            break

    # A prediction is calculated only when the latest period
    # ends with a main number.
    if history[-1] not in main_numbers:
        return "No Prediction"

    # Find the latest main number and the previous main number.
    latest_main_index = len(history) - 1
    previous_main_index = None

    for i in range(latest_main_index - 1, -1, -1):
        if history[i] in main_numbers:
            previous_main_index = i
            break

    if previous_main_index is None:
        return "No Prediction"

    # Count only the numbers strictly between the two main numbers.
    middle_numbers = history[previous_main_index + 1:latest_main_index]

    if not middle_numbers:
        return "No Prediction"

    big_count = sum(1 for n in middle_numbers if n >= 5)
    small_count = sum(1 for n in middle_numbers if n < 5)

    if big_count == small_count:
        return "No Prediction"
    return "Big" if big_count > small_count else "Small"


def predict_pattern_4(history):
    if len(history) < 2:
        return "No Prediction"
    small_combo = {0, 2, 4}
    big_combo = {5, 7, 9}

    if len(history) >= 3:
        last_3 = history[-3:]
        if all(n in small_combo for n in last_3) or all(n in big_combo for n in last_3):
            return "No Prediction"

    last_2 = history[-2:]
    if all(n in small_combo for n in last_2):
        base_result = "Small"
    elif all(n in big_combo for n in last_2):
        base_result = "Big"
    else:
        return "No Prediction"

    return base_result


def predict_new_combo_rules(history):
    if len(history) < 5:
        return "No Prediction"
    last_5 = [get_big_small(n) for n in history[-5:]]

    sequences = {
        ("Small", "Big", "Small", "Small", "Big"): "Big",
        ("Small", "Small", "Big", "Big", "Small"): "Big",
        ("Small", "Small", "Big", "Small", "Big"): "Big",
        ("Big", "Big", "Small", "Big", "Small"): "Small",
        ("Big", "Big", "Small", "Small", "Big"): "Small",
        ("Big", "Big", "Small", "Small", "Small"): "Big",
        ("Small", "Big", "Big", "Big", "Small"): "Small",
        ("Big", "Small", "Small", "Small", "Big"): "Big",
        ("Small", "Small", "Big", "Big", "Big"): "Small",
        ("Small", "Small", "Small", "Big", "Big"): "Small",
        ("Big", "Big", "Big", "Small", "Small"): "Big",
        # Point 12: Big, Big, Small, Big, Big -> Small
        ("Big", "Big", "Small", "Big", "Big"): "Small"
    }
    return sequences.get(tuple(last_5), "No Prediction")


def predict_sequence_rule(history):
    if len(history) < 2:
        return "No Prediction"
    a = history[-2]
    b = history[-1]

    if (b - a) % 10 == 1:
        result = get_big_small((b + 1) % 10)
    elif (a - b) % 10 == 1:
        result = get_big_small((b - 1) % 10)
    else:
        return "No Prediction"

    return result



def predict_streak_rule(history):
    # Rule 7: If the latest 3 results are the same Big/Small side,
    # continue the same side as the prediction. This also continues
    # when a 4th or later result is part of the same streak.
    if len(history) < 3:
        return "No Prediction"

    last_three = [get_big_small(n) for n in history[-3:]]

    if len(set(last_three)) != 1:
        return "No Prediction"

    return last_three[0]


def predict_additional_hot_digit(history):
    # Rule 9: Frequency Imbalance Rule.
    # Check the latest 10 Big/Small results. If one side has 7 or more
    # results, predict the opposite side. Otherwise, No Prediction.
    window_size = 10
    if len(history) < window_size:
        return "No Prediction"

    recent = [get_big_small(n) for n in history[-window_size:]]
    big_count = recent.count("Big")
    small_count = recent.count("Small")

    if big_count >= 7:
        return "Small"
    if small_count >= 7:
        return "Big"
    return "No Prediction"

def predict_additional_odd_even_last2(history):
    # Rule 10: last-two parity majority.
    if len(history) < 2:
        return "No Prediction"
    a, b = history[-2], history[-1]
    if a % 2 != b % 2:
        return "No Prediction"
    return "Big" if a % 2 == 1 else "Small"


def predict_additional_missing_number(history):
    # Rule 11: No Prediction through Period 31.
    # From Period 32 onward, use the first 31 periods as the fixed reference.
    if len(history) < 32:
        return "No Prediction"

    reference = history[:31]
    frequencies = {n: reference.count(n) for n in range(10)}
    missing = [n for n in range(10) if frequencies[n] == 0]

    # Always select a total of 5 numbers.
    # Missing numbers are selected first. If fewer than 5 are missing,
    # fill the remaining places with the lowest-frequency numbers.
    if len(missing) >= 5:
        selected = sorted(missing)[:5]
    else:
        selected = list(sorted(missing))
        remaining = [n for n in range(10) if n not in selected]
        remaining.sort(key=lambda n: (frequencies[n], n))
        selected.extend(remaining[:5 - len(selected)])

    big_count = sum(1 for n in selected if n >= 5)
    small_count = sum(1 for n in selected if n < 5)

    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"


def predict_additional_gap_number(history):
    # Rule 12: Use every previous occurrence of the latest number that
    # has an immediately following result. There is no 5-occurrence limit.
    # Majority Big -> opposite Small; majority Small -> opposite Big.
    # Equal -> No Prediction.
    if len(history) < 2:
        return "No Prediction"

    latest_number = history[-1]
    occurrence_indices = [
        i for i, n in enumerate(history[:-1]) if n == latest_number
    ]

    if not occurrence_indices:
        return "No Prediction"

    big_count = 0
    small_count = 0

    for i in occurrence_indices:
        next_result = get_big_small(history[i + 1])
        if next_result == "Big":
            big_count += 1
        else:
            small_count += 1

    if big_count > small_count:
        return "Small"
    if small_count > big_count:
        return "Big"
    return "No Prediction"


def predict_additional_position_middle(history):
    # Rule 13: Digit Gap Rule.
    # Take the latest digit's most recent repeat gap. Search earlier
    # occurrences of the same digit having the same gap, then use the
    # Big/Small result immediately following the second occurrence.
    # A majority decides; a tie gives No Prediction.
    if len(history) < 3:
        return "No Prediction"

    latest_digit = history[-1]
    previous_positions = [
        i for i in range(len(history) - 1)
        if history[i] == latest_digit
    ]

    if not previous_positions:
        return "No Prediction"

    latest_previous = previous_positions[-1]
    latest_gap = len(history) - 1 - latest_previous

    big_count = 0
    small_count = 0

    # Search historical pairs of the same digit separated by the same gap.
    # The second occurrence must have a following result available.
    for first in range(len(history) - latest_gap - 1):
        second = first + latest_gap
        if history[first] != latest_digit or history[second] != latest_digit:
            continue

        if second + 1 >= len(history):
            continue

        next_result = get_big_small(history[second + 1])
        if next_result == "Big":
            big_count += 1
        else:
            small_count += 1

    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"

def predict_additional_sum_number(history):
    # Rule 14: Check every supported consecutive Big/Small run pattern.
    # Patterns are BB, BBB, BBBB, SS, SSS, and SSSS. If the current
    # history ends with one or more of these patterns, search earlier
    # history for each applicable pattern and collect its following result.
    if len(history) < 3:
        return "No Prediction"

    categories = [get_big_small(n) for n in history]
    supported_patterns = [
        ("Big", "Big"),
        ("Big", "Big", "Big"),
        ("Big", "Big", "Big", "Big"),
        ("Small", "Small"),
        ("Small", "Small", "Small"),
        ("Small", "Small", "Small", "Small"),
    ]

    results = []
    for pattern in supported_patterns:
        size = len(pattern)
        if len(categories) < size or tuple(categories[-size:]) != pattern:
            continue

        for i in range(0, len(categories) - size):
            if tuple(categories[i:i + size]) == pattern:
                results.append(categories[i + size])

    if not results:
        return "No Prediction"

    big_count = results.count("Big")
    small_count = results.count("Small")
    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"


def predict_rolling_pattern_rule(history, window_size, min_occurrences=2):
    # Rolling Pattern Analysis:
    # Observe the latest N Big/Small results and search the complete
    # retained history for the same N-result pattern. Only earlier
    # occurrences with an immediately following result are considered.
    # At least two matching historical occurrences are required for a
    # strong prediction. A tie or insufficient evidence gives No Prediction.
    if len(history) < window_size + 1:
        return "No Prediction"

    latest_pattern = tuple(
        get_big_small(n) for n in history[-window_size:]
    )

    occurrences = []
    last_start = len(history) - window_size

    for i in range(0, last_start):
        pattern = tuple(
            get_big_small(n) for n in history[i:i + window_size]
        )
        if pattern == latest_pattern and i + window_size < len(history):
            occurrences.append(i)

    if len(occurrences) < min_occurrences:
        return "No Prediction"

    big_count = 0
    small_count = 0

    for i in occurrences:
        next_result = get_big_small(history[i + window_size])
        if next_result == "Big":
            big_count += 1
        else:
            small_count += 1

    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"


def predict_rolling_5_pattern(history):
    # Rule 8: every period, observe the latest 5 periods.
    return predict_rolling_pattern_rule(history, 5)


def predict_rolling_10_pattern(history):
    # Rule 15: latest 4 Big/Small outcomes, one historical occurrence needed.
    if len(history) < 5:
        return "No Prediction"

    latest_pattern = tuple(get_big_small(n) for n in history[-4:])
    for i in range(len(history) - 5, -1, -1):
        if tuple(get_big_small(n) for n in history[i:i + 4]) == latest_pattern:
            return get_big_small(history[i + 4])

    return "No Prediction"

def predict_transition_by_category(history, category_func, window_size=1):
    """Predict the next Big/Small result from a repeated categorical pattern."""
    if len(history) < window_size + 1:
        return "No Prediction"

    latest_category = category_func(history[-window_size:])
    big_count = 0
    small_count = 0

    last_start = len(history) - window_size
    for i in range(0, last_start):
        window = history[i:i + window_size]
        if category_func(window) != latest_category:
            continue

        next_result = get_big_small(history[i + window_size])
        if next_result == "Big":
            big_count += 1
        elif next_result == "Small":
            small_count += 1

    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"


def predict_rule_16(history):
    # Rule 16: Latest 3 Big/Small pattern -> use the 3 most recent
    # historical occurrences of the same pattern.
    if len(history) < 4:
        return "No Prediction"

    latest_pattern = tuple(get_big_small(n) for n in history[-3:])
    matches = []

    # Search only previous occurrences that have a following result.
    for i in range(len(history) - 4, -1, -1):
        if tuple(get_big_small(n) for n in history[i:i + 3]) != latest_pattern:
            continue

        next_result = get_big_small(history[i + 3])
        if next_result in ("Big", "Small"):
            matches.append(next_result)
            if len(matches) == 3:
                break

    if len(matches) < 3:
        return "No Prediction"

    big_count = matches.count("Big")
    small_count = matches.count("Small")

    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"


def predict_rule_17(history):
    # Rule 17: Direct pair mapping; no historical lookup.
    if len(history) < 2:
        return "No Prediction"

    last_two = tuple(get_big_small(n) for n in history[-2:])
    if last_two == ("Small", "Small"):
        return "Big"
    if last_two == ("Big", "Big"):
        return "Small"
    return "No Prediction"


def predict_rule_18(history):
    # Rule 18: Number-group missing-number streak.
    # Green group: 1,3,5,7,9 -> after 4 distinct group numbers, predict the missing one.
    # Red group: 0,2,4,6,8 -> after 4 distinct group numbers, predict the missing one.
    # Group 6,3,1,8 -> after 3 distinct group numbers, predict the missing one.
    # Group 0,2,4,5,7,9 -> after 5 distinct group numbers, predict the missing one.
    # Repeats inside the active group do not break the streak.
    # A number outside the active group breaks that streak; a fresh streak may form later.
    groups = [
        ({1, 3, 5, 7, 9}, 4),
        ({0, 2, 4, 6, 8}, 4),
        ({6, 3, 1, 8}, 3),
        ({0, 2, 4, 5, 7, 9}, 5),
    ]

    for group, required in groups:
        start = 0
        for i in range(len(history) - 1, -1, -1):
            if history[i] not in group:
                start = i + 1
                break

        distinct = set(history[start:])
        if len(distinct) >= required:
            missing = group - distinct
            if len(missing) == 1:
                return get_big_small(next(iter(missing)))

    return "No Prediction"


def predict_rule_19(history):
    # Rule 19: Latest 6 Big/Small pattern. One matching occurrence is enough.
    window_size = 6
    if len(history) < window_size + 1:
        return "No Prediction"
    latest_pattern = tuple(get_big_small(n) for n in history[-window_size:])
    for i in range(len(history) - window_size - 1, -1, -1):
        if tuple(get_big_small(n) for n in history[i:i + window_size]) == latest_pattern:
            return get_big_small(history[i + window_size])
    return "No Prediction"


def predict_rule_20(history):
    # Rule 20: Latest 7 Big/Small pattern. One matching occurrence is enough.
    window_size = 7
    if len(history) < window_size + 1:
        return "No Prediction"
    latest_pattern = tuple(get_big_small(n) for n in history[-window_size:])
    for i in range(len(history) - window_size - 1, -1, -1):
        if tuple(get_big_small(n) for n in history[i:i + window_size]) == latest_pattern:
            return get_big_small(history[i + window_size])
    return "No Prediction"


def predict_rule_21(history):
    # Rule 21: Transition Rule.
    # For the latest Big/Small result, count historical transitions from
    # that same result to the immediately following result. Majority wins;
    # a tie gives No Prediction.
    if len(history) < 2:
        return "No Prediction"

    current_result = get_big_small(history[-1])
    big_count = 0
    small_count = 0

    for i in range(len(history) - 1):
        if get_big_small(history[i]) != current_result:
            continue

        next_result = get_big_small(history[i + 1])
        if next_result == "Big":
            big_count += 1
        else:
            small_count += 1

    if big_count > small_count:
        return "Big"
    if small_count > big_count:
        return "Small"
    return "No Prediction"

# Only Rules 3, 5 and 12 are globally reversed.
OPPOSITE_RULE_INDICES = {2, 4, 11}

def reverse_selected_rule_predictions(predictions):
    reversed_predictions = list(predictions)
    for index in OPPOSITE_RULE_INDICES:
        if index >= len(reversed_predictions):
            continue
        if reversed_predictions[index] == "Big":
            reversed_predictions[index] = "Small"
        elif reversed_predictions[index] == "Small":
            reversed_predictions[index] = "Big"
    return reversed_predictions

def get_last_20(history):
    return history[-20:] if len(history) >= 20 else []


def get_missing_numbers(history):
    data = get_last_20(history)
    if len(data) < 20:
        return []
    present = set(data)
    return [n for n in range(10) if n not in present]


def get_gap_numbers(history):
    data = get_last_20(history)
    if not data:
        return []
    result = []
    for n in range(10):
        if n in data:
            gap = len(data) - 1 - max(i for i, x in enumerate(data) if x == n)
        else:
            gap = len(data)
        result.append((n, gap))
    result.sort(key=lambda x: (-x[1], x[0]))
    return result


def get_pair_patterns(history):
    data = get_last_20(history)
    pairs = {}
    for i in range(len(data) - 1):
        pair = (data[i], data[i + 1])
        pairs[pair] = pairs.get(pair, 0) + 1
    return sorted(pairs.items(), key=lambda x: (-x[1], x[0]))


def get_position_numbers(history):
    data = get_last_20(history)
    if not data:
        return {"First": None, "Middle": None, "Last": None}
    return {
        "First": data[0],
        "Middle": data[len(data) // 2],
        "Last": data[-1]
    }


def get_sum_number(history):
    data = get_last_20(history)
    if len(data) < 2:
        return None
    return (data[-2] + data[-1]) % 10



def get_last_50_big_small_counts(history):
    """Cumulative Big/Small count starting from Period 50.
    Period 50 counts 1-50; Period 51 counts 1-51;
    Period 52 counts 1-52, and so on indefinitely.
    """
    if len(history) < 50:
        return None

    big_count = sum(1 for n in history if get_big_small(n) == "Big")
    small_count = len(history) - big_count
    return big_count, small_count

def calculate_backup_number(history):
    if len(history) < 3:
        return None

    alternative_period = history[-3]
    latest_period = history[-1]
    gap = (latest_period - alternative_period) % 10

    return (latest_period + gap) % 10


def backup_matches_rule_1(history, rule_1_prediction, rule_3_prediction):
    if rule_1_prediction not in ("Big", "Small"):
        return False
    if rule_3_prediction not in ("Big", "Small"):
        return False
    if rule_1_prediction != rule_3_prediction:
        return False

    backup_number = calculate_backup_number(history)
    if backup_number is None:
        return False

    backup_prediction = get_big_small(backup_number)
    return (
        rule_1_prediction == backup_prediction
        and rule_3_prediction == backup_prediction
    )


def high_chances_additional_main_rule(history, rule_1_prediction):
    # HIGH CHANCES applies when the current period itself is a trigger
    # OR when the immediately previous period was a trigger.
    # Trigger numbers: 6, 3, 1, 8.
    # Rule 1 Small + Backup 0-4 -> HIGH CHANCES.
    # Rule 1 Big   + Backup 5-9 -> HIGH CHANCES.
    # Otherwise -> no HIGH CHANCES.
    if not history or rule_1_prediction not in ("Big", "Small"):
        return False

    trigger_numbers = {6, 3, 1, 8}

    eligible = (
        history[-1] in trigger_numbers
        or (
            len(history) >= 2
            and history[-2] in trigger_numbers
        )
    )

    if not eligible:
        return False

    backup_number = calculate_backup_number(history)
    if backup_number is None:
        return False

    if rule_1_prediction == "Small" and 0 <= backup_number <= 4:
        return True

    if rule_1_prediction == "Big" and 5 <= backup_number <= 9:
        return True

    return False



def calculate_final_result(predictions):
    valid_votes = [p for p in predictions if p in ("Big", "Small")]
    if not valid_votes:
        return "No Prediction"
    big_c = valid_votes.count("Big")
    small_c = valid_votes.count("Small")
    if big_c > small_c: return "Big"
    if small_c > big_c: return "Small"
    return "Big and Small"


# =========================================================
# NEW PREMIUM 3D GLOSSY BALL DESIGN WIDGET
# =========================================================

class NumberCircle(Button):

    def __init__(self, number, number_color, split_colors=None, **kwargs):
        super().__init__(**kwargs)

        self.number = str(number)
        self.number_color = number_color
        self.split_colors = split_colors

        self.size_hint_y = None
        self.height = dp(75)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)

        self.text = self.number
        self.color = number_color
        self.font_size = "26sp"
        self.bold = True

        with self.canvas.before:
            # 1. Soft Outer Shadow Ring
            self.shadow_color = Color(0, 0, 0, 0.06)
            self.shadow_ellipse = Ellipse()

            # 2. Main Outer Colored Spherical Border
            self.outer_color = Color(1, 1, 1, 1)
            self.outer_circle = Ellipse()

            # 3. Secondary Split Layer (For 0 & 5)
            self.second_color = Color(1, 1, 1, 1)
            self.second_circle = Ellipse()

            # 4. Premium White Inner Core Capsule
            self.inner_color = Color(0.98, 0.98, 0.98, 1)
            self.inner_circle = Ellipse()

            # 5. Top Glossy Shine Reflection Arc (3D Glass Look)
            self.shine_color = Color(1, 1, 1, 0.45)
            self.shine_ellipse = Ellipse()

        self.bind(pos=self.update_circle, size=self.update_circle)

    def update_circle(self, *args):
        # Calculate dynamic bounds perfectly matching proportions
        ball_size = min(self.width, self.height) * 0.92
        x = self.center_x - ball_size / 2
        y = self.center_y - ball_size / 2

        # Draw Outer Soft Drop Shadow
        self.shadow_color.rgba = (0, 0, 0, 0.05)
        self.shadow_ellipse.pos = (x, y - dp(2))
        self.shadow_ellipse.size = (ball_size, ball_size)

        # Setup base color structure matching split logic perfectly
        if self.split_colors and len(self.split_colors) >= 2:
            c1 = self.split_colors[0]
            c2 = self.split_colors[1]

            # Left side split rendering
            self.outer_color.rgb = (c1[0], c1[1], c1[2])
            self.outer_circle.pos = (x, y)
            self.outer_circle.size = (ball_size, ball_size)
            self.outer_circle.angle_start = 0
            self.outer_circle.angle_end = 180

            # Right side split rendering
            self.second_color.rgb = (c2[0], c2[1], c2[2])
            self.second_circle.pos = (x, y)
            self.second_circle.size = (ball_size, ball_size)
            self.second_circle.angle_start = 180
            self.second_circle.angle_end = 360
        else:
            # Solid sphere filling format
            self.outer_color.rgb = (self.number_color[0], self.number_color[1], self.number_color[2]) if hasattr(self.number_color, '__len__') else (0.8, 0.1, 0.1)
            self.outer_circle.pos = (x, y)
            self.outer_circle.size = (ball_size, ball_size)
            self.outer_circle.angle_start = 0
            self.outer_circle.angle_end = 360
            
            # Deactivate second layer logic
            self.second_color.rgba = (0, 0, 0, 0)
            self.second_circle.size = (0, 0)

        # Draw Premium Inner Sphere Core Frame (Creates the clean circular mask inside)
        inner_size = ball_size * 0.76
        ix = self.center_x - inner_size / 2
        iy = self.center_y - inner_size / 2
        
        # Subtle light gray/white radial base to mimic image gradients
        self.inner_color.rgba = (0.96, 0.98, 0.98, 1)
        self.inner_circle.pos = (ix, iy)
        self.inner_circle.size = (inner_size, inner_size)

        # Draw Top Glass Reflection Highlight Accent Layer
        shine_w = inner_size * 0.85
        shine_h = inner_size * 0.4
        sx = self.center_x - shine_w / 2
        sy = (iy + inner_size) - shine_h - dp(2)
        
        self.shine_color.rgba = (1, 1, 1, 0.6)
        self.shine_ellipse.pos = (sx, sy)
        self.shine_ellipse.size = (shine_w, shine_h)
# =========================================================
# MAIN APP
# =========================================================

class WingoPredictorApp(App):

    def build(self):

        self.history = []
        self.period_counts = []
        self.final_history = []
        self.rule_prediction_history = []
        self.rule_wins = [0] * 21
        self.rule_losses = [0] * 21
        self.losing_streak = 0

        # 50-period warning/restart cycle state.
        # Each 50-period block is independent: 1-50, 51-100, 101-150, ...
        self.warning_count = 0
        self.restart_pending = False
        self.restart_triggered = False
        self.warning_event = None

        # =================================================
        # SCROLL VIEW
        # =================================================

        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )

        # =================================================
        # MAIN CONTENT
        # =================================================

        content = BoxLayout(
            orientation="vertical",
            padding=[
                dp(12),
                dp(18),
                dp(12),
                dp(25)
            ],
            spacing=dp(10),
            size_hint_y=None
        )

        content.bind(
            minimum_height=content.setter(
                "height"
            )
        )

        # =================================================
        # TITLE
        # =================================================

        title = Label(
            text="WINGO SMART PREDICTOR",
            font_size="24sp",
            bold=True,
            color=(
                1,
                0.75,
                0,
                1
            ),
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(title)

        # =================================================
        # NEXT PREDICTION
        # =================================================

        next_title = Label(
            text="NEXT PREDICTION",
            font_size="22sp",
            bold=True,
            color=(
                0,
                0.35,
                0.05,
                1
            ),
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(next_title)

        # =================================================
        # WAITING / PREDICTION STATUS
        # =================================================

        self.result_label = Label(
            text="Waiting...",
            font_size="25sp",
            bold=True,
            color=(
                0.70,
                0.50,
                0,
                1
            ),
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(
            self.result_label
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(8)
            )
        )

        # =================================================
        # SELECT NUMBERS
        # =================================================

        select_label = Label(
            text="SELECT NUMBERS",
            font_size="21sp",
            bold=True,
            color=(
                0,
                0.15,
                0.45,
                1
            ),
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(
            select_label
        )

        # =================================================
        # NUMBER GRID
        # =================================================

        number_grid = GridLayout(
            cols=5,
            rows=2,
            spacing=[
                dp(5),
                dp(20)
            ],
            padding=[
                dp(4),
                dp(5),
                dp(4),
                dp(5)
            ],
            size_hint_y=None,
            height=dp(200),
            row_default_height=dp(82),
            row_force_default=True
        )

        # =================================================
        # COLORS
        # =================================================

        GREEN = (
            0.0,
            0.70,
            0.35,
            1
        )

        RED = (
            0.90,
            0.05,
            0.08,
            1
        )

        VIOLET = (
            0.50,
            0.05,
            0.90,
            1
        )

        # =================================================
        # NUMBERS 0 - 9
        # =================================================

        btn = NumberCircle(
            0,
            VIOLET,
            split_colors=[
                VIOLET,
                RED
            ]
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(0)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            1,
            GREEN
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(1)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            2,
            RED
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(2)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            3,
            GREEN
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(3)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            4,
            RED
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(4)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            5,
            VIOLET,
            split_colors=[
                VIOLET,
                GREEN
            ]
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(5)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            6,
            RED
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(6)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            7,
            GREEN
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(7)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            8,
            RED
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(8)
        )
        number_grid.add_widget(btn)

        btn = NumberCircle(
            9,
            GREEN
        )
        btn.bind(
            on_release=lambda x:
            self.number_clicked(9)
        )
        number_grid.add_widget(btn)

        content.add_widget(
            number_grid
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(10)
            )
        )

        # =================================================
        # LAST 20 PERIODS
        # =================================================

        history_title = Label(
            text="LAST 20 PERIODS",
            font_size="20sp",
            bold=True,
            color=(
                0.03,
                0.15,
                0.45,
                1
            ),
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(
            history_title
        )

        # =================================================
        # HISTORY GRID
        # =================================================

        self.history_grid = GridLayout(
            cols=2,
            spacing=[
                dp(10),
                dp(5)
            ],
            padding=[
                dp(5),
                dp(2)
            ],
            size_hint_y=None
        )

        self.history_grid.bind(
            minimum_height=self.history_grid.setter(
                "height"
            )
        )

        history_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint_y=None,
            height=dp(150)
        )

        history_scroll.add_widget(
            self.history_grid
        )

        content.add_widget(
            history_scroll
        )

        # =================================================
        # WARNING
        # =================================================

        self.warning_label = Label(
            text="",
            font_size="19sp",
            bold=True,
            color=(1.0, 0.45, 0.45, 1),
            size_hint_y=None,
            height=dp(34)
        )

        content.add_widget(
            self.warning_label
        )


        # =================================================
        # LAST 50 BIG / SMALL COUNT
        # =================================================

        self.last_50_count_title = Label(
            text="BIG / SMALL COUNT FROM PERIOD 1",
            font_size="18sp",
            bold=True,
            color=(0.03, 0.15, 0.45, 1),
            size_hint_y=None,
            height=dp(36)
        )

        content.add_widget(self.last_50_count_title)

        self.last_50_count_label = Label(
            text="Waiting... Count starts from Period 50",
            font_size="16sp",
            bold=True,
            color=(0.70, 0.50, 0, 1),
            size_hint_y=None,
            height=dp(34),
            halign="left",
            valign="middle"
        )
        self.last_50_count_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        content.add_widget(self.last_50_count_label)

        # =================================================
        # PREDICTION RULES
        # =================================================

        rules_title = Label(
            text="21 PREDICTION RULES",
            font_size="20sp",
            bold=True,
            color=(
                1,
                0.85,
                0,
                1
            ),
            size_hint_y=None,
            height=dp(42)
        )

        self.rules_box = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            size_hint_y=None
        )

        self.rules_box.bind(
            minimum_height=self.rules_box.setter(
                "height"
            )
        )

        # =================================================
        # FINAL RESULT
        # =================================================

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(8)
            )
        )

        self.final_label = Label(
            text="FINAL RESULT",
            font_size="23sp",
            bold=True,
            markup=True,
            color=(
                0.0,
                0.65,
                0.20,
                1
            ),
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(
            self.final_label
        )

        self.losing_streak_label = Label(
            text="LOSING STREAK: 0",
            font_size="19sp",
            bold=True,
            color=(0.90, 0.05, 0.08, 1),
            size_hint_y=None,
            height=dp(38)
        )

        content.add_widget(
            self.losing_streak_label
        )

        # =================================================
        # BACKUP NUMBER
        # =================================================

        self.backup_label = Label(
            text="BACKUP NUMBER",
            font_size="20sp",
            bold=True,
            markup=True,
            color=(
                0.10,
                0.30,
                0.75,
                1
            ),
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(
            self.backup_label
        )

        # =================================================
        # HIGH CHANCES
        # =================================================

        self.high_chances_label = Label(
            text="",
            font_size="21sp",
            bold=True,
            color=(
                0.95,
                0.45,
                0.00,
                1
            ),
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(
            self.high_chances_label
        )

        # =================================================
        # PREDICTION RULES
        # =================================================

        content.add_widget(
            rules_title
        )

        content.add_widget(
            self.rules_box
        )

        # =================================================
        # RESET + DELETE LAST (UNCHANGED RESET FUNCTION)
        # =================================================

        reset_row = BoxLayout(
            orientation="horizontal",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(48)
        )

        reset_button = Button(
            text="RESET",
            font_size="17sp",
            bold=True,
            size_hint_x=0.75,
            background_normal="",
            background_color=(
                0.80,
                0.10,
                0.10,
                1
            ),
            color=(
                1,
                1,
                1,
                1
            )
        )

        reset_button.bind(
            on_release=lambda x:
            self.reset_all()
        )

        delete_button = Button(
            text="×",
            font_size="25sp",
            bold=True,
            size_hint_x=0.25,
            background_normal="",
            background_color=(
                0.55,
                0.00,
                0.00,
                1
            ),
            color=(
                1,
                1,
                1,
                1
            )
        )

        delete_button.bind(
            on_release=lambda x:
            self.delete_last_number()
        )

        reset_row.add_widget(reset_button)
        reset_row.add_widget(delete_button)

        content.add_widget(reset_row)

        # =================================================
        # INITIAL DISPLAY
        # =================================================

        self.update_history_display()
        self.update_last_50_count()

        self.clear_predictions()

        # =================================================
        # PUT CONTENT INSIDE SCROLL
        # =================================================

        scroll.add_widget(
            content
        )

        return scroll

    # =====================================================
    # RULE WIN / LOSS TRACKING
    # =====================================================

    def update_rule_scores(self, actual_number):
        actual_result = get_big_small(actual_number)
        if not self.rule_prediction_history:
            return

        previous_predictions = self.rule_prediction_history[-1]
        for i, prediction in enumerate(previous_predictions[:21]):
            if prediction == actual_result:
                self.rule_wins[i] += 1
            elif prediction in ("Big", "Small"):
                self.rule_losses[i] += 1

    def undo_last_rule_score(self):
        if len(self.history) < 1 or len(self.rule_prediction_history) < 2:
            return

        actual_result = get_big_small(self.history[-1])
        previous_predictions = self.rule_prediction_history[-2]
        for i, prediction in enumerate(previous_predictions[:21]):
            if prediction == actual_result:
                if self.rule_wins[i] > 0:
                    self.rule_wins[i] -= 1
            elif prediction in ("Big", "Small"):
                if self.rule_losses[i] > 0:
                    self.rule_losses[i] -= 1

    # =====================================================
    # 50-PERIOD WARNING / RESTART
    # =====================================================

    def start_new_50_period_block(self, period_number):
        # Non-overlapping blocks: 1-50, 51-100, 101-150, ...
        if period_number >= 1 and (period_number - 1) % 50 == 0:
            self.warning_count = 0
            self.restart_pending = False
            self.restart_triggered = False
            self.warning_label.text = ""

    def show_warning(self, warning_number):
        if self.warning_event is not None:
            self.warning_event.cancel()
            self.warning_event = None

        self.warning_label.text = "WARNING " + str(warning_number)
        self.warning_label.color = (1.0, 0.45, 0.45, 1)

        self.warning_event = Clock.schedule_once(
            lambda dt: self.hide_warning(),
            15
        )

    def hide_warning(self):
        self.warning_label.text = ""
        self.warning_event = None

    def check_50_period_warning(self):
        # A warning is generated only when the losing streak reaches 5.
        if self.losing_streak == 5:
            self.warning_count += 1

            if self.warning_count == 1:
                self.show_warning(1)
            elif self.warning_count == 2:
                self.show_warning(2)
                # The next generated prediction is the one to watch.
                self.restart_pending = True

    def trigger_restart(self):
        self.restart_pending = False
        self.restart_triggered = True

        self.final_label.text = (
            "[color=#0066FF][b]RESTART[/b][/color]"
        )
        self.final_label.color = (0.0, 0.40, 1.0, 1)

        self.result_label.text = "No Prediction"
        self.result_label.color = (0.55, 0.55, 0.55, 1)

        self.backup_label.text = "BACKUP NUMBER"
        self.high_chances_label.text = ""

        self.clear_predictions()

    # =====================================================
    # NUMBER CLICK
    # =====================================================

    def number_clicked(self, number):

        # IMPORTANT:
        # DO NOT LIMIT HISTORY TO 20.
        # Every new period is stored.

        next_period_number = len(self.history) + 1
        self.start_new_50_period_block(next_period_number)

        # Compare the newly entered result with the PREVIOUS period's
        # Final Result. Backup Number is never used for losing streak.
        if self.final_history:
            previous_final = self.final_history[-1]
            actual_result = get_big_small(number)

            if previous_final in ("Big", "Small"):
                if actual_result == previous_final:
                    self.losing_streak = 0
                else:
                    self.losing_streak += 1

                self.losing_streak_label.text = (
                    "LOSING STREAK: " + str(self.losing_streak)
                )

                # Check the current 50-period block for the first/second
                # time the losing streak reaches 5.
                self.check_50_period_warning()

                # After WARNING 2, prediction continues normally.
                # Do NOT restart just because the immediately entered result
                # happens to win. Restart only when the losing streak has
                # returned to zero after WARNING 2.
                if self.restart_pending and self.losing_streak == 0:
                    self.trigger_restart()

        # Score every rule using the prediction made for the previous period.
        self.update_rule_scores(number)

        self.history.append(number)

        period_number = len(
            self.history
        )

        self.period_counts.append(
            period_number
        )

        self.update_history_display()
        self.update_last_50_count()

        # Once RESTART is triggered, no new prediction is generated
        # for the remainder of that 50-period block.
        if self.restart_triggered:
            self.result_label.text = "No Prediction"
            self.result_label.color = (0.55, 0.55, 0.55, 1)
            self.final_label.text = "[color=#0066FF][b]RESTART[/b][/color]"
            self.final_label.color = (0.0, 0.40, 1.0, 1)
            self.backup_label.text = "BACKUP NUMBER"
            self.high_chances_label.text = ""
            self.clear_predictions()
            self.final_history.append(None)
            return

        # -----------------------------------------------
        # WAITING
        # -----------------------------------------------

        if len(self.history) < 20:

            remaining = (
                20 - len(self.history)
            )

            self.result_label.text = (
                "Waiting... "
                + str(remaining)
                + " more"
            )

            self.result_label.color = (
                0.70,
                0.50,
                0,
                1
            )

            p8_early = predict_rolling_5_pattern(self.history)
            p11_early = predict_additional_missing_number(self.history)
            p15_early = predict_rolling_10_pattern(self.history)
            p16_early = predict_rule_16(self.history)
            p17_early = predict_rule_17(self.history)
            early_predictions = ["No Prediction"] * 21
            early_predictions[7] = p8_early
            early_predictions[10] = p11_early
            early_predictions[14] = p15_early
            early_predictions[15] = p16_early
            early_predictions[16] = p17_early
            early_predictions[17] = "No Prediction"
            self.rule_prediction_history.append(early_predictions[:])
            self.show_predictions(early_predictions)

            self.final_history.append(None)
            return

        # -----------------------------------------------
        # PREDICTION RULES
        # -----------------------------------------------

        p1 = predict_pattern_1(
            self.history
        )

        p2 = predict_pattern_2(
            self.history,
            self.period_counts
        )

        p3 = predict_pattern_3(
            self.history
        )

        p4 = predict_pattern_4(
            self.history
        )

        p5 = predict_new_combo_rules(
            self.history
        )

        p6 = predict_sequence_rule(
            self.history
        )

        p7 = predict_streak_rule(
            self.history
        )

        p8 = predict_rolling_5_pattern(self.history)
        p9 = predict_additional_hot_digit(self.history)
        p10 = predict_additional_odd_even_last2(self.history)
        p11 = predict_additional_missing_number(self.history)
        p12 = predict_additional_gap_number(self.history)
        p13 = predict_additional_position_middle(self.history)
        p14 = predict_additional_sum_number(self.history)
        p15 = predict_rolling_10_pattern(self.history)
        p16 = predict_rule_16(self.history)
        p17 = predict_rule_17(self.history)
        p18 = predict_rule_18(self.history)
        p19 = predict_rule_19(self.history)
        p20 = predict_rule_20(self.history)
        p21 = predict_rule_21(self.history)

        predictions = [
            p1, p2, p3, p4, p5, p6, p7, p8,
            p9, p10, p11, p12, p13, p14, p15,
            p16, p17, p18, p19, p20, p21
        ]

        # Reverse only the rules whose current Loss count is higher than Wins.
        predictions = reverse_selected_rule_predictions(predictions)

        self.rule_prediction_history.append(predictions[:])

        self.show_predictions(
            predictions
        )

        # -----------------------------------------------
        # FINAL
        # -----------------------------------------------

        # Final Result uses all active Rules 1-21.
        final = calculate_final_result(
            predictions
        )

        if final == "Big":
            final_result_color = "FFD900"
        elif final == "Small":
            final_result_color = "33BFFF"
        else:
            final_result_color = "00A633"

        self.final_label.text = (
            "[color=#00A633]FINAL RESULT: [/color]"
            + "[color=#"
            + final_result_color
            + "][b]"
            + final
            + "[/b][/color]"
        )
        self.final_label.color = (0.0, 0.65, 0.20, 1)

        # -----------------------------------------------
        # BACKUP NUMBER + HIGH CHANCES
        # -----------------------------------------------

        backup_number = calculate_backup_number(
            self.history
        )

        if backup_number is None:
            self.backup_label.text = "BACKUP NUMBER"
        else:
            backup_colors = {
                0: "9B00FF", 1: "00B34D", 2: "E60015",
                3: "00B34D", 4: "E60015", 5: "9B00FF",
                6: "E60015", 7: "00B34D", 8: "E60015",
                9: "00B34D"
            }
            self.backup_label.text = (
                "BACKUP NUMBER: [color=#"
                + backup_colors[backup_number]
                + "][b]"
                + str(backup_number)
                + "[/b][/color]"
            )

        high_chances = None

        # HIGH CHANCES is shown only when FINAL RESULT is Big or Small.
        # If FINAL RESULT is Big and Small, HIGH CHANCES is not shown.
        if (
            final in ("Big", "Small")
            and high_chances_additional_main_rule(
                self.history,
                p1
            )
        ):
            high_chances = p1

        if high_chances is not None:
            self.high_chances_label.text = "HIGH CHANCES"

            # HIGH CHANCES is only an indicator. It does NOT reverse FINAL RESULT.
        else:
            self.high_chances_label.text = ""

        # Store the FINAL RESULT that will be checked against the next
        # entered Big/Small result. Backup Number is not stored here.
        self.final_history.append(
            final if final in ("Big", "Small") else None
        )

        self.result_label.text = (
            "Prediction Ready"
        )

        self.result_label.color = (
            0,
            0.35,
            0.05,
            1
        )

    # =====================================================
    # HISTORY DISPLAY
    # =====================================================

    def update_history_display(self):

        self.history_grid.clear_widgets()

        # =================================================
        # ONLY DISPLAY THE LATEST 20 PERIODS
        # HISTORY ITSELF IS NOT LIMITED
        # =================================================

        total = len(self.history)

        start_index = max(
            0,
            total - 20
        )

        visible_periods = list(
            range(
                start_index,
                total
            )
        )

        # Split latest 20 into two columns:
        # first 10 on left, next 10 on right

        left_periods = visible_periods[:10]
        right_periods = visible_periods[10:]

        max_rows = max(
            len(left_periods),
            len(right_periods)
        )

        for row in range(max_rows):

            # -------------------------------------------
            # LEFT COLUMN
            # -------------------------------------------

            if row < len(left_periods):

                index = left_periods[row]

                number = self.history[index]

                period_number = index + 1

                text = (
                    "Period "
                    + str(period_number)
                    + " : "
                    + str(number)
                    + "  "
                    + get_big_small(number)
                )

            else:

                text = ""

            number_color = {
                0: "9B00FF",
                1: "00B34D",
                2: "E60015",
                3: "00B34D",
                4: "E60015",
                5: "9B00FF",
                6: "E60015",
                7: "00B34D",
                8: "E60015",
                9: "00B34D"
            }
            big_small_color = "FFD900" if number >= 5 else "33BFFF"
            history_markup = (
                "[color=#30303D]Period "
                + str(period_number)
                + " : [/color][color=#"
                + number_color[number]
                + "][b]"
                + str(number)
                + "[/b][/color]  [color=#"
                + big_small_color
                + "][b]"
                + get_big_small(number)
                + "[/b][/color]"
            ) if text else ""

            left_label = Label(
                text=history_markup,
                markup=True,
                font_size="14sp",
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(28)
            )

            left_label.bind(
                size=lambda instance,
                value: setattr(
                    instance,
                    "text_size",
                    value
                )
            )

            self.history_grid.add_widget(
                left_label
            )

            # -------------------------------------------
            # RIGHT COLUMN
            # -------------------------------------------

            if row < len(right_periods):

                right_index = right_periods[row]
                right_number = self.history[right_index]
                right_period_number = right_index + 1
                right_big_small_color = "FFD900" if right_number >= 5 else "33BFFF"

                right_history_markup = (
                    "[color=#30303D]Period "
                    + str(right_period_number)
                    + " : [/color][color=#"
                    + number_color[right_number]
                    + "][b]"
                    + str(right_number)
                    + "[/b][/color]  [color=#"
                    + right_big_small_color
                    + "][b]"
                    + get_big_small(right_number)
                    + "[/b][/color]"
                )
            else:
                right_history_markup = ""

            right_label = Label(
                text=right_history_markup,
                markup=True,
                font_size="14sp",
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(28)
            )

            right_label.bind(
                size=lambda instance,
                value: setattr(
                    instance,
                    "text_size",
                    value
                )
            )

            self.history_grid.add_widget(
                right_label
            )


    # =====================================================
    # LAST 50 BIG / SMALL COUNT DISPLAY
    # =====================================================

    def update_last_50_count(self):
        counts = get_last_50_big_small_counts(self.history)

        if counts is None:
            remaining = 50 - len(self.history)
            self.last_50_count_label.text = (
                "Waiting... Count starts from Period 50 ("
                + str(remaining)
                + " more)"
            )
            self.last_50_count_label.color = (0.70, 0.50, 0, 1)
            return

        big_count, small_count = counts
        current_period = len(self.history)
        self.last_50_count_label.text = (
            "PERIOD " + str(current_period)
            + " (1-" + str(current_period) + "): "
            + "BIG: " + str(big_count)
            + "    SMALL: " + str(small_count)
            + "    LOSING STREAK: " + str(self.losing_streak)
        )
        self.last_50_count_label.color = (0.03, 0.15, 0.45, 1)

    # =====================================================
    # CLEAR RULES
    # =====================================================

    def clear_predictions(self):

        self.rules_box.clear_widgets()

        rule_numbers = list(range(1, 22))

        for i in rule_numbers:

            rule_label = Label(
                text=(
                    "Rule " + str(i)
                    + "    W: " + str(self.rule_wins[i - 1])
                    + "    L: " + str(self.rule_losses[i - 1])
                ),
                font_size="17sp",
                bold=True,
                color=(
                    1.0,
                    0.20,
                    0.65,
                    1
                ),
                size_hint_y=None,
                height=dp(28)
            )

            result_label = Label(
                text="No Prediction",
                font_size="15sp",
                color=(
                    0.20,
                    0.20,
                    0.30,
                    1
                ),
                size_hint_y=None,
                height=dp(28)
            )

            self.rules_box.add_widget(
                rule_label
            )

            self.rules_box.add_widget(
                result_label
            )

            if i != 21:

                self.rules_box.add_widget(
                    Widget(
                        size_hint_y=None,
                        height=dp(5)
                    )
                )

    # =====================================================
    # SHOW PREDICTIONS
    # =====================================================

    def show_predictions(
        self,
        predictions
    ):

        self.rules_box.clear_widgets()

        rule_numbers = list(range(1, 22))

        for i, prediction in zip(rule_numbers, predictions):

            rule_label = Label(
                text=(
                    "Rule " + str(i)
                    + "    W: " + str(self.rule_wins[i - 1])
                    + "    L: " + str(self.rule_losses[i - 1])
                ),
                font_size="17sp",
                bold=True,
                color=(
                    1.0,
                    0.20,
                    0.65,
                    1
                ),
                size_hint_y=None,
                height=dp(28)
            )

            if prediction == "Big":

                prediction_color = (
                    1.0,
                    0.85,
                    0.0,
                    1
                )

            elif prediction == "Small":

                prediction_color = (
                    0.20,
                    0.75,
                    1.0,
                    1
                )

            else:

                prediction_color = (
                    0.25,
                    0.25,
                    0.30,
                    1
                )

            result_label = Label(
                text=prediction,
                font_size="15sp",
                bold=True,
                color=prediction_color,
                size_hint_y=None,
                height=dp(28)
            )

            self.rules_box.add_widget(
                rule_label
            )

            self.rules_box.add_widget(
                result_label
            )

            if i != 21:

                self.rules_box.add_widget(
                    Widget(
                        size_hint_y=None,
                        height=dp(6)
                    )
                )

    # =====================================================
    # DELETE LAST NUMBER
    # =====================================================

    def delete_last_number(self):

        if not self.history:
            return

        # Remove the score produced by the deleted period.
        self.undo_last_rule_score()

        self.history.pop()

        if self.period_counts:
            self.period_counts.pop()

        if self.final_history:
            self.final_history.pop()

        if self.rule_prediction_history:
            self.rule_prediction_history.pop()

        # Rebuild the losing streak from the remaining entered results
        # and the Final Result that preceded each result.
        self.losing_streak = 0
        for i in range(1, len(self.history)):
            previous_final = self.final_history[i - 1] if i - 1 < len(self.final_history) else None
            actual_result = get_big_small(self.history[i])
            if previous_final in ("Big", "Small"):
                if actual_result == previous_final:
                    self.losing_streak = 0
                else:
                    self.losing_streak += 1
        self.losing_streak_label.text = (
            "LOSING STREAK: " + str(self.losing_streak)
        )

        self.update_history_display()
        self.update_last_50_count()

        if len(self.history) < 20:
            remaining = 20 - len(self.history)
            self.result_label.text = (
                "Waiting... " + str(remaining) + " more"
            )
            self.result_label.color = (
                0.70,
                0.50,
                0,
                1
            )
            self.final_label.text = "FINAL RESULT"
            self.backup_label.text = "BACKUP NUMBER"
            self.high_chances_label.text = ""
            p8_early = predict_rolling_5_pattern(self.history)
            p11_early = predict_additional_missing_number(self.history)
            p15_early = predict_rolling_10_pattern(self.history)
            p16_early = predict_rule_16(self.history)
            p17_early = predict_rule_17(self.history)
            early_predictions = ["No Prediction"] * 21
            early_predictions[7] = p8_early
            early_predictions[10] = p11_early
            early_predictions[14] = p15_early
            early_predictions[15] = p16_early
            early_predictions[16] = p17_early
            early_predictions[17] = "No Prediction"
            early_predictions = reverse_selected_rule_predictions(early_predictions)
            if self.rule_prediction_history:
                self.rule_prediction_history[-1] = early_predictions[:]
                self.show_predictions(early_predictions)
            else:
                self.clear_predictions()
            return

        # Recalculate exactly as if the deleted period had never been entered.
        p1 = predict_pattern_1(self.history)
        p2 = predict_pattern_2(self.history, self.period_counts)
        p3 = predict_pattern_3(self.history)
        p4 = predict_pattern_4(self.history)
        p5 = predict_new_combo_rules(self.history)
        p6 = predict_sequence_rule(self.history)
        p7 = predict_streak_rule(self.history)
        p8 = predict_rolling_5_pattern(self.history)
        p9 = predict_additional_hot_digit(self.history)
        p10 = predict_additional_odd_even_last2(self.history)
        p11 = predict_additional_missing_number(self.history)
        p12 = predict_additional_gap_number(self.history)
        p13 = predict_additional_position_middle(self.history)
        p14 = predict_additional_sum_number(self.history)
        p15 = predict_rolling_10_pattern(self.history)
        p16 = predict_rule_16(self.history)
        p17 = predict_rule_17(self.history)
        p18 = predict_rule_18(self.history)
        p19 = predict_rule_19(self.history)
        p20 = predict_rule_20(self.history)
        p21 = predict_rule_21(self.history)
        predictions = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21]
        predictions = reverse_selected_rule_predictions(predictions)
        if self.rule_prediction_history:
            self.rule_prediction_history[-1] = predictions[:]
        else:
            self.rule_prediction_history.append(predictions[:])
        self.show_predictions(predictions)

        # Final Result uses all active Rules 1-21.
        final = calculate_final_result(predictions)
        if final == "Big":
            final_result_color = "FFD900"
        elif final == "Small":
            final_result_color = "33BFFF"
        else:
            final_result_color = "00A633"
        self.final_label.text = (
            "[color=#00A633]FINAL RESULT: [/color]"
            + "[color=#" + final_result_color + "][b]"
            + final + "[/b][/color]"
        )
        self.final_label.color = (0.0, 0.65, 0.20, 1)

        backup_number = calculate_backup_number(self.history)
        if backup_number is None:
            self.backup_label.text = "BACKUP NUMBER"
        else:
            backup_colors = {
                0: "9B00FF", 1: "00B34D", 2: "E60015",
                3: "00B34D", 4: "E60015", 5: "9B00FF",
                6: "E60015", 7: "00B34D", 8: "E60015",
                9: "00B34D"
            }
            self.backup_label.text = (
                "BACKUP NUMBER: [color=#"
                + backup_colors[backup_number]
                + "][b]" + str(backup_number)
                + "[/b][/color]"
            )

        high_chances = None
        if (
            final in ("Big", "Small")
            and high_chances_additional_main_rule(self.history, p1)
        ):
            high_chances = p1

        if high_chances is not None:
            self.high_chances_label.text = "HIGH CHANCES"

            # HIGH CHANCES is only an indicator. It does NOT reverse FINAL RESULT.
        else:
            self.high_chances_label.text = ""

        self.result_label.text = "Prediction Ready"
        self.result_label.color = (0, 0.35, 0.05, 1)

    # =====================================================
    # RESET
    # =====================================================

    def reset_all(self):

        self.history = []

        self.period_counts = []
        self.final_history = []
        self.rule_prediction_history = []
        self.rule_wins = [0] * 21
        self.rule_losses = [0] * 21
        self.losing_streak = 0

        if self.warning_event is not None:
            self.warning_event.cancel()
            self.warning_event = None

        self.warning_count = 0
        self.restart_pending = False
        self.restart_triggered = False
        self.warning_label.text = ""
        self.losing_streak_label.text = "LOSING STREAK: 0"

        self.result_label.text = (
            "Waiting..."
        )

        self.result_label.color = (
            0.70,
            0.50,
            0,
            1
        )

        self.final_label.text = (
            "FINAL RESULT"
        )

        self.final_label.color = (
            1,
            0.35,
            0,
            1
        )

        self.backup_label.text = "BACKUP NUMBER"
        self.high_chances_label.text = ""

        self.update_history_display()
        self.update_last_50_count()

        self.clear_predictions()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    WingoPredictorApp().run()