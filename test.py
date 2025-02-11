def max_in_array(arr):
    return max(arr)
def test_max_in_array():
    tests = [
        ([1, 2, 3, 4], 4),
        ([-1, -2, -3, -4], -1),
        ([5], 5),
        ([0, 0, 0], 0)
    ]
    
    for i, (input_data, expected) in enumerate(tests):
        try:
            assert max_in_array(input_data) == expected
            print(f"Test {i + 1} passed")
        except AssertionError:
            print(f"Test {i + 1} failed")

test_max_in_array()