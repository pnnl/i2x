import numpy as np


def get_nums(state = None):
    
    random_state = np.random.RandomState()
    if state is not None:
        random_state.set_state(state)
    
    state = random_state.get_state(random_state)

    return  state, random_state.randint(0, 100000, 100)


if __name__ == "__main__":

    out = {}
    # first round
    out[1] = get_nums()
    
    # second round, shouldn't match first round
    out[2] = get_nums()

    # third round, should match first round
    out[3] = get_nums(state = out[1][0])

    print(f"Comparing 1 to 2 (should NOT match): {np.all(out[1][1] == out[2][1])}")
    print(f"Comparing 1 and 3 (should match): {np.all(out[1][1] == out[3][1])}")