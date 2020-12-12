import threading


class Tester():
    @staticmethod
    def run_test(test):
        tt = threading.Thread(target=test, name="test_thread")
        tt.start()
        tt.join()

