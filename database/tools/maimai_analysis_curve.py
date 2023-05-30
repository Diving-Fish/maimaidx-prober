diff_weights = {
    "1":    [0.7, 0.1, 0.1, 0.1],
    "2":    [0.7, 0.1, 0.1, 0.1],
    "3":    [0.7, 0.1, 0.1, 0.1],
    "4":    [0.7, 0.1, 0.1, 0.1],
    "5":    [0.7, 0.1, 0.1, 0.1],
    "6":    [0.7, 0.1, 0.1, 0.1],
    "7":    [0.7, 0.1, 0.1, 0.1],
    "7+":   [0.7, 0.1, 0.1, 0.1],
    "8":    [0.7, 0.1, 0.1, 0.1],
    "8+":   [0.7, 0.1, 0.1, 0.1],
    "9":    [0.7, 0.1, 0.1, 0.1],
    "9+":   [0.7, 0.1, 0.1, 0.1],
    "10":   [0.7, 0.1, 0.1, 0.1],
    "10+":  [0.7, 0.1, 0.1, 0.1],
    "11":   [0.7, 0.1, 0.1, 0.1],
    "11+":  [0.7, 0.1, 0.1, 0.1],
    "15":   [0.7, 0.1, 0.1, 0.1],
    "12":  [0.5, 0.2, 0.2, 0.1],
    "12+":   [0.4, 0.2, 0.2, 0.2],
    "13":  [0.3, 0.2, 0.2, 0.3],
    "13+":   [0.3, 0.1, 0.25, 0.35],
    "14":  [0.3, 0.0, 0.3, 0.4],
    "14+":   [0.2, 0.0, 0.35, 0.45]
}

def achievement_curve(diff: float):
    if diff <= -4:
        return -0.5
    elif diff < -1:
        return -0.1 + 0.1 * diff
    elif diff < 1:
        return 0.2 * diff
    elif diff < 4:
        return 0.1 + 0.1 * diff
    return 0.5

def percent_curve(diff: float):
    if diff < -0.6:
        return -0.25 + 0.25 * diff
    elif diff < -0.2:
        return -0.1 + 0.5 * diff
    elif diff < 0.3:
        return diff
    elif diff < 0.9:
        return 0.15 + 0.5 * diff
    return 0.42 + 0.2 * diff

def get_diff(difficulty, diff_ach, diff_s, diff_sss, diff_sssp):
    print(float(diff_ach), float(diff_s), float(diff_sss), float(diff_sssp))
    if difficulty[-1] == "+":
        diff = int(difficulty[:-1]) + 0.75
    else:
        diff = int(difficulty) + 0.25
    weight = diff_weights[difficulty]
    return diff - achievement_curve(float(diff_ach)) * weight[0] - percent_curve(float(diff_s)) * weight[1] - percent_curve(float(diff_sss)) * weight[2] - percent_curve(float(diff_sssp)) * weight[3] 
