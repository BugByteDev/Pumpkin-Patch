"""Opt-in CI checks of the compiled app; uses isolated throwaway user data."""
import json,os,sys,tempfile,time,traceback
from pathlib import Path


def run(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    (output/'progress.json').write_text(json.dumps({'stage':'loading runtime'}))
    isolated=tempfile.TemporaryDirectory(prefix='pumpkin-smoke-')
    os.environ['PUMPKIN_DATA']=str(Path(isolated.name)/'data')
    # A CI-only Mesa driver lets the Windows runner exercise the real shader.
    # It is outside the distributable and never changes installed system drivers.
    dll_handle=None
    if sys.platform=='win32' and os.environ.get('PUMPKIN_CI_OPENGL_DIR'):
        import ctypes
        driver=Path(os.environ['PUMPKIN_CI_OPENGL_DIR'])
        dll_handle=os.add_dll_directory(str(driver))
        ctypes.WinDLL(str(driver/'opengl32.dll'))
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QSurfaceFormat,QFontDatabase
    from PySide6.QtWidgets import QApplication
    import native
    from OpenGL.GL import glGetString,GL_VERSION,GL_RENDERER
    from storage import validate,write_guide
    from mesh import export
    import numpy as np
    fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile);fmt.setDepthBufferSize(24);fmt.setSamples(4);QSurfaceFormat.setDefaultFormat(fmt)
    app=QApplication([sys.argv[0]]);QFontDatabase.addApplicationFont(str(native.ROOT/'assets/fonts/PatrickHand-Regular.ttf'));app.setFont(native.font(19))
    (output/'progress.json').write_text(json.dumps({'stage':'creating window'}))
    window=native.Patch();window.show()
    result={'platform':sys.platform,'frozen':bool(getattr(sys,'frozen',False)),'checks':[]}
    state=0;deadline=time.monotonic()+120;poll=QTimer()
    def finish(error=None):
        poll.stop()
        result['ok']=error is None
        if error:result['error']=error
        (output/'smoke.json').write_text(json.dumps(result,indent=2))
        window.close();app.exit(1 if error else 0)
    def tick():
        nonlocal state
        try:
            (output/'progress.json').write_text(json.dumps({'stage':state,'program':bool(window.view.program),'objects':len(window.view.objects),'job':window.job is not None,'revision':window.revision,'wanted':window.want_revision,'status':window.message}))
            if time.monotonic()>deadline:raise TimeoutError('App did not finish building/rendering within 120 seconds')
            if window.view.error:raise RuntimeError(window.view.error)
            if window.delay.isActive() or window.job is not None or window.revision!=window.want_revision:return
            if not window.view.program or not window.view.objects or window.view.pending is not None:return
            if state==0:
                result['checks'].append('blank pumpkin rendered through spawned mesh worker')
                window.apply_preset(24);state=1;return
            if state==1:
                result['checks'].append('scary preset rendered')
                window.add_cut([[-.15,.08],[.15,.08],[.15,-.08],[-.15,-.08]])
                state=2;return
            if state==2:
                result['checks'].append('freehand cut rendered')
                window.toggle_glow();window.view.yaw=.35;window.view.pitch=.1;window.view.update();state=3;return
            if state==3:
                frame=window.view.grabFramebuffer()
                if frame.isNull():raise RuntimeError('The OpenGL framebuffer is empty')
                rgba=frame.convertToFormat(frame.Format.Format_RGBA8888)
                pixels=np.frombuffer(rgba.constBits(),np.uint8).reshape(rgba.height(),rgba.width(),4)
                pumpkin=(pixels[:,:,0]>150)&(pixels[:,:,1]<190)&(pixels[:,:,3]>0)
                if int(pumpkin.sum())<1000:raise RuntimeError('No orange pumpkin pixels in the rendered framebuffer')
                window.view.makeCurrent()
                result['opengl_version']=glGetString(GL_VERSION).decode()
                result['opengl_renderer']=glGetString(GL_RENDERER).decode();window.view.doneCurrent()
                window.grab().save(str(output/'editor.png'))
                result['checks'].append('lit and rotated pumpkin, shader and framebuffer verified')
                export(window.d,output/'test-pumpkin.glb')
                (output/'test-pumpkin.pumpkin').write_text(json.dumps(window.d))
                assert validate(json.loads((output/'test-pumpkin.pumpkin').read_text()))==window.d
                (output/'carving-guide.html').write_text(write_guide(window.d),encoding='utf-8')
                result['checks'].append('GLB, editable save roundtrip and guide exported')
                window.save();window.gallery();state=4;return
            if state==4:
                window.grab().save(str(output/'gallery.png'));window.close_overlay();window.help();state=5;return
            if state==5:
                window.grab().save(str(output/'info.png'));window.close_overlay()
                result['checks'].append('saved gallery and info panels opened')
                finish()
        except Exception:finish(traceback.format_exc())
    poll.timeout.connect(tick);poll.start(200)
    code=app.exec();isolated.cleanup()
    return code
