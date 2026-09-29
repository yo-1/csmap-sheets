class CancelledError(RuntimeError):
    pass


def check_cancel(feedback):
    if feedback is not None and feedback.isCanceled():
        raise CancelledError('処理をキャンセルしました。部分成果は未完了です。')


def report(feedback, message, percent=None):
    check_cancel(feedback)
    if feedback is None:
        print(message, flush=True)
    else:
        feedback.pushInfo(message)
        if percent is not None:
            feedback.setProgress(percent)


def gdal_progress(feedback, start=0, end=25):
    def callback(fraction, message, data):
        if feedback is not None:
            if feedback.isCanceled():
                return 0
            feedback.setProgress(start+(end-start)*fraction)
        return 1
    return callback
