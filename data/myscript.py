import solar_trace as st
import qu as qu

def test_main_function_execution():
    # This test will simply run the main function and will pass if no exceptions are raised.
    qu.qu_driver()
    st.st_driver()  