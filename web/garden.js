// An inline CCv2 renderer. Dependencies are pinned, locally served public assets.
export default function ({parentElement}) {
  const root = parentElement.querySelector('.garden');
  const stage = parentElement.querySelector('.garden-stage');
  let disposed = false, renderer, scene, camera, garden, gsapContext;
  let onScreen = true, lastFrame = 0;
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  const assetBase = () => {
    const cloud = location.pathname.indexOf('/~/+/');
    const prefix = cloud >= 0 ? location.pathname.slice(0, cloud + 5)
      : location.pathname.startsWith('/streamlit/') ? '/streamlit/' : '/';
    return new URL(prefix + 'app/static/vendor/', location.origin);
  };
  const getGSAP = () => {
    if (window.gsap) return Promise.resolve(window.gsap);
    if (!window.__steadyGSAP) {
      window.__steadyGSAP = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = new URL('gsap.min.js', assetBase()).href;
        script.onload = () => resolve(window.gsap);
        script.onerror = () => { script.remove(); window.__steadyGSAP = null; reject(new Error('Animation asset unavailable')); };
        document.head.append(script);
      });
    }
    return window.__steadyGSAP;
  };
  const render = () => { if (!disposed && renderer) renderer.render(scene, camera); };
  function setPlayback() {
    if (!renderer || disposed) return;
    renderer.setAnimationLoop(null);
    if (document.hidden || !onScreen) { gsapContext?.getTweens().forEach(tween => tween.pause()); root.dataset.playing = 'false'; return; }
    if (preference.matches) {
      gsapContext?.revert(); gsapContext = null;
      garden.rotation.y = -.15; garden.position.y = 0;
      root.dataset.playing = 'false'; render(); return;
    }
    gsapContext?.getTweens().forEach(tween => tween.resume());
    root.dataset.playing = 'true';
    renderer.setAnimationLoop(time => {
      // 30fps and limited pixel density keep the decorative scene inexpensive.
      if (time - lastFrame < 32) return;
      lastFrame = time; render();
    });
  }
  function animate(gsap) {
    if (!gsap || disposed || preference.matches) return;
    gsapContext?.revert();
    gsapContext = gsap.context(() => {
      gsap.from(stage, {opacity:0, y:10, duration:.85, ease:'power2.out'});
      gsap.to(garden.rotation, {y:.16, duration:9, ease:'sine.inOut', yoyo:true, repeat:-1});
      gsap.to(garden.position, {y:.045, duration:4.5, ease:'sine.inOut', yoyo:true, repeat:-1});
    }, root);
  }
  const resize = new ResizeObserver(() => {
    if (!renderer || disposed) return;
    const width = stage.clientWidth, height = stage.clientHeight;
    if (!width || !height) return;
    const aspect = width / height;
    camera.left = -2.55 * aspect; camera.right = 2.55 * aspect;
    camera.top = 2.55; camera.bottom = -2.55;
    camera.updateProjectionMatrix(); renderer.setSize(width, height, false); render();
  });
  resize.observe(stage);
  const visibility = new IntersectionObserver(entries => { onScreen = entries[0].isIntersecting; setPlayback(); }, {threshold:.05});
  visibility.observe(root);
  const onMotion = () => { if (!preference.matches && window.gsap && garden) animate(window.gsap); setPlayback(); };
  const onVisibility = () => setPlayback();
  preference.addEventListener('change', onMotion);
  document.addEventListener('visibilitychange', onVisibility);
  const onLost = event => { event.preventDefault(); renderer?.setAnimationLoop(null); root.dataset.garden = 'fallback'; root.dataset.playing = 'false'; };
  const onRestored = () => { if (!disposed) { root.dataset.garden = 'webgl'; setPlayback(); render(); } };
  async function init() {
    try {
      const THREE = await import(new URL('three.module.js', assetBase()).href);
      if (disposed) return;
      renderer = new THREE.WebGLRenderer({antialias:true, alpha:true, powerPreference:'low-power'});
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.55;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.domElement.setAttribute('aria-hidden','true');
      renderer.domElement.addEventListener('webglcontextlost', onLost);
      renderer.domElement.addEventListener('webglcontextrestored', onRestored);
      stage.append(renderer.domElement);
      scene = new THREE.Scene();
      camera = new THREE.OrthographicCamera(-3,3,2.55,-2.55,.1,40);
      camera.position.set(5,4.1,7); camera.lookAt(0,1.35,0);
      scene.add(new THREE.HemisphereLight(0xfff8ec,0x71825e,3));
      const sun = new THREE.DirectionalLight(0xffeedc,4);
      sun.position.set(-3,7,4); sun.castShadow = true;
      sun.shadow.mapSize.set(512,512);
      sun.shadow.camera.left = sun.shadow.camera.bottom = -4;
      sun.shadow.camera.right = sun.shadow.camera.top = 4;
      sun.shadow.bias = -.002; sun.shadow.normalBias = .04;
      scene.add(sun);
      const fill = new THREE.DirectionalLight(0xe5eed9,2); fill.position.set(4,2,-3); scene.add(fill);
      garden = new THREE.Group(); garden.rotation.y = -.15; scene.add(garden);
      const material = (color, roughness=.72) => new THREE.MeshStandardMaterial({color, roughness, metalness:0});
      const base = new THREE.Mesh(new THREE.CylinderGeometry(1.8,1.8,.14,72),material(0xd0dac0));
      base.position.y = .08; base.receiveShadow = true; garden.add(base);
      const pebble = (color, scale, position, angle) => {
        const mesh = new THREE.Mesh(new THREE.SphereGeometry(1,48,32),material(color,.63));
        mesh.scale.set(...scale); mesh.position.set(...position); mesh.rotation.set(.08,angle,.07);
        mesh.castShadow = mesh.receiveShadow = true; garden.add(mesh); return mesh;
      };
      pebble(0x6b8052,[1.17,.45,.83],[-.08,.58,0],.35);
      pebble(0xd4c3a4,[.9,.34,.7],[.1,1.2,.03],-.3);
      pebble(0xd49369,[.57,.38,.51],[-.02,1.77,.01],.22);
      const stemCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-.03,2.03,.01),new THREE.Vector3(.02,2.3,.02),new THREE.Vector3(-.015,2.7,.015)]);
      const stem = new THREE.Mesh(new THREE.TubeGeometry(stemCurve,20,.019,8,false),material(0x4f713c));
      stem.castShadow = true; garden.add(stem);
      const leaf = (color, x, y, z, rotation) => {
        const mesh = new THREE.Mesh(new THREE.SphereGeometry(1,32,20),material(color,.61));
        mesh.scale.set(.17,.39,.045); mesh.position.set(x,y,z); mesh.rotation.set(.18,.3,rotation);
        mesh.castShadow = true; garden.add(mesh);
      };
      leaf(0x7d9956,-.18,2.54,.02,.75);
      leaf(0x93ac67,.19,2.75,.015,-.65);
      pebble(0xc4ceac,[.15,.1,.12],[1.4,.25,.3],.2);
      pebble(0xb2c198,[.1,.07,.08],[-1.45,.21,-.2],0);
      const disc = new THREE.Mesh(new THREE.CircleGeometry(.81,64),new THREE.MeshBasicMaterial({color:0xf2d9bb,side:THREE.DoubleSide}));
      disc.position.set(.9,2.5,-.9); disc.quaternion.copy(camera.quaternion); scene.add(disc);
      root.dataset.garden = 'webgl';
      const width = stage.clientWidth, height = stage.clientHeight;
      camera.left = -2.55 * width / height; camera.right = 2.55 * width / height;
      camera.updateProjectionMatrix(); renderer.setSize(width,height,false); render();
      let gsap;
      try { gsap = await getGSAP(); } catch { /* The garden remains usable without motion assets. */ }
      if (disposed) return;
      animate(gsap); setPlayback();
    } catch {
      root.dataset.garden = 'fallback'; root.dataset.playing = 'false';
      if (renderer) { renderer.setAnimationLoop(null); renderer.dispose(); renderer.domElement.remove(); }
    } finally {
      if (!disposed) root.dataset.ready = 'true';
    }
  }
  init();
  return () => {
    disposed = true; resize.disconnect(); visibility.disconnect();
    preference.removeEventListener('change',onMotion); document.removeEventListener('visibilitychange',onVisibility);
    gsapContext?.revert();
    renderer?.setAnimationLoop(null);
    scene?.traverse(object => {
      object.geometry?.dispose();
      if (object.material) (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => material.dispose());
    });
    if (renderer) {
      renderer.domElement.removeEventListener('webglcontextlost',onLost);
      renderer.domElement.removeEventListener('webglcontextrestored',onRestored);
      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove();
    }
  };
}
