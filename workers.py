"""Isolate mesh/preview work from Qt so a slow carving cannot freeze its UI."""
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

class WorkPool:
    def __init__(self):self.executor=None
    def submit(self,fn,*args,**kwargs):
        if self.executor is None:
            self.executor=ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'))
        try:return self.executor.submit(fn,*args,**kwargs)
        except BrokenProcessPool:
            self.shutdown(wait=False,cancel_futures=True)
            self.executor=ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'))
            return self.executor.submit(fn,*args,**kwargs)
    def shutdown(self,wait=True,cancel_futures=False):
        if self.executor is not None:
            processes=list((getattr(self.executor,'_processes',None) or {}).values())
            self.executor.shutdown(wait=wait,cancel_futures=cancel_futures);self.executor=None
            if not wait:
                for process in processes:
                    if process.is_alive():process.terminate()

def build_model(design):
    from model_cache import build_cached
    return build_cached(design)

def render_preview(design,stem_only,path):
    from thumbnails import _generate
    from PySide6.QtCore import QBuffer,QIODevice
    image=_generate(design,stem_only,path)
    buffer=QBuffer();buffer.open(QIODevice.WriteOnly);image.save(buffer,'PNG')
    return bytes(buffer.data())
