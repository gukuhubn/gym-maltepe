/* TRIMODE GYM — kütle modeli (three.js UMD, build adımı yok)
   Ölçüler data/dimensions.json'dan gelir; hiçbir geometri elle yazılmaz. */
(function (global) {
  const T = global.THREE;

  /* Plan koordinatı (x, y) → sahne (x, yükseklik, z=y).
     ExtrudeGeometry XY düzleminde üretilir; rotateX(-90°) sonrası
     (X,Y,Z) → (X, Z, -Y) olduğundan şekli -y ile kuruyoruz ki z = +plan_y olsun. */
  function shapeFrom(poly, holes) {
    const s = new T.Shape(poly.map(p => new T.Vector2(p[0], -p[1])));
    (holes || []).forEach(hl => s.holes.push(new T.Path(hl.map(p => new T.Vector2(p[0], -p[1])))));
    return s;
  }
  function slab(poly, y, t, mat, holes) {
    const g = new T.ExtrudeGeometry(shapeFrom(poly, holes), { depth: t, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    const m = new T.Mesh(g, mat); m.position.y = y; m.receiveShadow = true; m.castShadow = false;
    return m;
  }
  function prism(poly, y, hgt, mat, shadow) {
    const g = new T.ExtrudeGeometry(shapeFrom(poly), { depth: hgt, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    const m = new T.Mesh(g, mat); m.position.y = y;
    m.castShadow = shadow !== false; m.receiveShadow = true;
    return m;
  }
  function offsetRing(ring, d) {           // basit dışa ötelenmiş çokgen (duvar bandı)
    const n = ring.length, out = [];
    let a2 = 0;
    for (let i = 0; i < n; i++) { const a = ring[i], b = ring[(i + 1) % n]; a2 += a[0] * b[1] - b[0] * a[1]; }
    const sgn = a2 > 0 ? 1 : -1;
    for (let i = 0; i < n; i++) {
      const p = ring[(i - 1 + n) % n], c = ring[i], q = ring[(i + 1) % n];
      const n1 = nrm(p, c), n2 = nrm(c, q);
      let bx = n1[0] + n2[0], by = n1[1] + n2[1];
      const L = Math.hypot(bx, by) || 1; bx /= L; by /= L;
      const cosHalf = Math.max(0.35, (n1[0] * bx + n1[1] * by));
      out.push([c[0] + sgn * bx * d / cosHalf, c[1] + sgn * by * d / cosHalf]);
    }
    return out;
    function nrm(a, b) { const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1; return [dy / L, -dx / L]; }
  }

  function build(D, stil, opts) {
    opts = opts || {};
    const S = D.stiller[stil] || D.stiller.endustriyel;
    const H = D.tavan_h, root = new T.Group();
    const mat = (c, r, m) => new T.MeshStandardMaterial({
      color: new T.Color(c), roughness: r === undefined ? 0.85 : r, metalness: m || 0.0 });

    // — zemin bölgeleri
    D.bolgeler.forEach(b => root.add(slab(b.poligon, 0, 0.02, mat(b.renk3d || b.renk, 0.93))));
    // — ıslak hacim zeminleri
    Object.values(D.islak).forEach(bl => Object.values(bl).forEach(
      h => root.add(slab(h.poligon, 0, 0.02, mat("#B9C9D2", 0.28)))));

    // — kabuk duvarları (dış bant)
    const wallMat = mat(S.duvar, 0.95);
    ["salon", "erkek", "kadin"].forEach(k => {
      const ring = D.kabuk[k], out = offsetRing(ring, D.duvar_t);
      const g = new T.ExtrudeGeometry(shapeFrom(out, [ring.slice().reverse()]),
                                      { depth: H, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
      const m = new T.Mesh(g, wallMat); m.position.y = 0;
      m.castShadow = true; m.receiveShadow = true; root.add(m);
    });
    // — salon / soyunma arası bölme
    ["erkek", "kadin"].forEach(k => {
      const ring = D.kabuk[k], out = offsetRing(ring, 0.05);
      const g = new T.ExtrudeGeometry(shapeFrom(out, [ring.slice().reverse()]),
                                      { depth: H, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
      const m = new T.Mesh(g, wallMat.clone()); m.position.y = 0; root.add(m);
    });
    // — ıslak hacim iç bölmeleri (h = 2,40)
    Object.values(D.islak).forEach(bl => ["dus", "wc"].forEach(n => {
      const ring = bl[n].poligon, out = offsetRing(ring, 0.05);
      const g = new T.ExtrudeGeometry(shapeFrom(out, [ring.slice().reverse()]),
                                      { depth: 2.4, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
      const m = new T.Mesh(g, mat("#E9EDF0", 0.9)); m.position.y = 0;
      m.castShadow = true; root.add(m);
    }));

    // — tavan
    root.add(slab(D.kabuk.salon, H, 0.06, mat(S.tavan, 0.98)));

    // — altıgen arena rig (4 katman)
    const [cx, cy] = D.hex.merkez, s = D.hex.kenar, akMat = mat(S.aksan, 0.45, 0.35);
    for (let lay = 0; lay < 4; lay++) {
      const r = s * (1 - lay * 0.18), yh = 0.25 + lay * 0.40;
      for (let i = 0; i < 6; i++) {
        const a1 = Math.PI / 2 + i * Math.PI / 3, a2 = a1 + Math.PI / 3;
        const p1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
        const p2 = [cx + r * Math.cos(a2), cy + r * Math.sin(a2)];
        const L = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
        const bar = new T.Mesh(new T.BoxGeometry(L, 0.09, 0.09), akMat);
        bar.position.set((p1[0] + p2[0]) / 2, yh, (p1[1] + p2[1]) / 2);
        bar.rotation.y = -Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);
        bar.castShadow = true; root.add(bar);
      }
    }
    for (let i = 0; i < 6; i++) {                       // köşe dikmeleri
      const a = Math.PI / 2 + i * Math.PI / 3;
      const col = new T.Mesh(new T.CylinderGeometry(0.055, 0.055, 1.75, 12), akMat);
      col.position.set(cx + s * Math.cos(a), 0.875, cy + s * Math.sin(a));
      col.castShadow = true; root.add(col);
    }

    // — ekipman kütleleri
    const ekMat = mat(S.ekipman, 0.62, 0.15);
    D.ekipman.forEach(e => { if (e.kod !== "A") root.add(prism(e.poligon, 0.02, e.h, ekMat)); });
    // — sabit mobilya
    D.mobilya.forEach(m => root.add(prism(m.poligon, 0.02, m.h,
      mat(m.tip === "banko" ? S.aksan : "#E6E1D8", 0.8))));

    // — cephe doğraması (cam)
    const cam = new T.MeshPhysicalMaterial({ color: 0xDCEAF4, roughness: 0.04, metalness: 0.0,
      transmission: 0.92, thickness: 0.02, transparent: true, opacity: 0.18,
      side: T.DoubleSide });
    const cerceve = mat("#2B3036", 0.5, 0.4);
    D.cephe.forEach(seg => {
      const [a, b] = seg, L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const ang = -Math.atan2(b[1] - a[1], b[0] - a[0]);
      const g = new T.Mesh(new T.BoxGeometry(L, 2.4, 0.05), cam);
      g.position.set((a[0] + b[0]) / 2, 1.35, (a[1] + b[1]) / 2);
      g.rotation.y = ang; root.add(g);
      for (const yy of [0.14, 2.56]) {                       // doğrama profilleri
        const f = new T.Mesh(new T.BoxGeometry(L, 0.09, 0.09), cerceve);
        f.position.set((a[0] + b[0]) / 2, yy, (a[1] + b[1]) / 2);
        f.rotation.y = ang; root.add(f);
      }
      const nx = Math.max(1, Math.round(L / 1.15));
      for (let i = 1; i < nx; i++) {
        const tt = i / nx, px = a[0] + (b[0] - a[0]) * tt, pz = a[1] + (b[1] - a[1]) * tt;
        const f = new T.Mesh(new T.BoxGeometry(0.07, 2.42, 0.07), cerceve);
        f.position.set(px, 1.35, pz); f.rotation.y = ang; root.add(f);
      }
    });

    // — lineer LED armatürler + ışık
    const ledMat = new T.MeshBasicMaterial({ color: new T.Color(S.isik) });
    D.aydinlatma.forEach((p, i) => {
      const bar = new T.Mesh(new T.BoxGeometry(1.25, 0.06, 0.12), ledMat);
      bar.position.set(p[0], H - 0.30, p[1]); root.add(bar);
      if (i % 2 === 0) {
        const pl = new T.PointLight(new T.Color(S.isik), 0.42, 7.5, 2.0);
        pl.position.set(p[0], H - 0.45, p[1]); root.add(pl);
      }
    });

    // — genel ışık
    root.add(new T.AmbientLight(0xffffff, stil === "minimal" ? 0.70 : 0.48));
    root.add(new T.HemisphereLight(0xE8F0F8, 0x2A2E33, stil === "minimal" ? 0.55 : 0.35));
    const sun = new T.DirectionalLight(0xFFF2E0, stil === "minimal" ? 1.15 : 0.85);
    sun.position.set(-11, 8, 2); sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    const d0 = 14, sc = sun.shadow.camera;
    sc.left = -d0; sc.right = d0; sc.top = d0; sc.bottom = -d0; sc.near = 0.5; sc.far = 40;
    root.add(sun);
    return root;
  }

  global.GymModel = { build: build };
})(window);
