/* TRIMODE GYM — kütle modeli (three.js UMD, build adımı yok)
   Ölçüler data/dimensions.json'dan gelir; hiçbir geometri elle yazılmaz. */
(function (global) {
  let T = null;

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
    T = global.THREE;
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

    // — ALTIGEN RİNG: kanvas platform + 6 pedli direk + 4 sıra halat
    var RG = D.ring, cx = RG.merkez[0], cy = RG.merkez[1], s6 = RG.kenar;
    var kose = [];
    for (var i6 = 0; i6 < 6; i6++) {
      var a6 = Math.PI / 2 + i6 * Math.PI / 3;
      kose.push([cx + s6 * Math.cos(a6), cy + s6 * Math.sin(a6)]);
    }
    var platMat = mat("#1C2024", 0.92);           // şok emici taban
    var kanvas  = mat(stil === "minimal" ? "#C9C3B4" : "#9C968A", 0.96);
    var celik   = mat("#22262A", 0.45, 0.55);
    var ped     = mat("#8E2B26", 0.72, 0.05);     // ring köşe pedi — koyu kırmızı vinil
    var bantM   = mat("#1A1D20", 0.78, 0.10);     // platform kenar bandı
    var seritM  = mat("#8E2B26", 0.7, 0.05);
    var halatM  = mat("#15181B", 0.62, 0.1);
    // platform (hafif yükseltilmiş) + kanvas üst yüzey
    var ringPoly = kose.map(function (p) { return [p[0], p[1]]; });
    root.add(prism(ringPoly, 0.02, RG.platform_h - 0.04, platMat));
    root.add(slab(ringPoly, RG.platform_h - 0.02, 0.03, kanvas));
    // platform kenar bandı
    for (var e6 = 0; e6 < 6; e6++) {
      var p1 = kose[e6], p2 = kose[(e6 + 1) % 6];
      var L6 = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
      var ac6 = -Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);
      var bant = new T.Mesh(new T.BoxGeometry(L6, 0.22, 0.05), bantM);
      bant.position.set((p1[0] + p2[0]) / 2, RG.platform_h - 0.13, (p1[1] + p2[1]) / 2);
      bant.rotation.y = ac6; bant.castShadow = true; root.add(bant);
      var ser = new T.Mesh(new T.BoxGeometry(L6, 0.035, 0.055), seritM);
      ser.position.set((p1[0] + p2[0]) / 2, RG.platform_h - 0.05, (p1[1] + p2[1]) / 2);
      ser.rotation.y = ac6; root.add(ser);
    }
    // 6 köşe direği — çelik gövde + pedli kılıf
    kose.forEach(function (p) {
      var dh = RG.direk_h;
      var dir = new T.Mesh(new T.CylinderGeometry(0.045, 0.045, dh + 0.18, 14), celik);
      dir.position.set(p[0], RG.platform_h + (dh + 0.18) / 2, p[1]);
      dir.castShadow = true; root.add(dir);
      var kilif = new T.Mesh(new T.CylinderGeometry(0.085, 0.085, dh * 0.92, 16), ped);
      kilif.position.set(p[0], RG.platform_h + dh * 0.46 + 0.04, p[1]);
      kilif.castShadow = true; root.add(kilif);
      var bas = new T.Mesh(new T.SphereGeometry(0.055, 14, 10), celik);
      bas.position.set(p[0], RG.platform_h + dh + 0.20, p[1]); root.add(bas);
    });
    // 4 sıra halat — her kenarda, hafif sarkma ile
    RG.halat_kotlari.forEach(function (kot) {
      for (var e7 = 0; e7 < 6; e7++) {
        var q1 = kose[e7], q2 = kose[(e7 + 1) % 6];
        var y0 = RG.platform_h + kot;
        var cv = new T.CatmullRomCurve3([
          new T.Vector3(q1[0], y0, q1[1]),
          new T.Vector3((q1[0] + q2[0]) / 2, y0 - 0.035, (q1[1] + q2[1]) / 2),
          new T.Vector3(q2[0], y0, q2[1])]);
        var hm = new T.Mesh(new T.TubeGeometry(cv, 10, 0.028, 8, false), halatM);
        hm.castShadow = true; root.add(hm);
      }
    });
    // — ekipman: tipe göre tanınır kütle (kutu değil)
    const ekMat  = mat(S.ekipman, 0.55, 0.35);
    const ekAks  = mat(S.aksan, 0.5, 0.25);
    const ekKoyu = mat("#141719", 0.7, 0.2);
    function merkezVeEksen(poly) {
      let cx0 = 0, cy0 = 0; poly.forEach(p => { cx0 += p[0]; cy0 += p[1]; });
      cx0 /= poly.length; cy0 /= poly.length;
      let best = 0, bp = [poly[0], poly[1]];
      for (let i = 0; i < poly.length; i++) {
        const a = poly[i], b = poly[(i + 1) % poly.length];
        const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (L > best) { best = L; bp = [a, b]; }
      }
      const ang = -Math.atan2(bp[1][1] - bp[0][1], bp[1][0] - bp[0][0]);
      let kisa = 1e9;
      for (let i = 0; i < poly.length; i++) {
        const a = poly[i], b = poly[(i + 1) % poly.length];
        const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (L < kisa) kisa = L;
      }
      return { cx: cx0, cy: cy0, uzun: best, kisa: kisa, ang: ang };
    }
    function kutu(g, w, hgt, d, mt, x, y, z) {
      const m = new T.Mesh(new T.BoxGeometry(w, hgt, d), mt);
      m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; g.add(m); return m;
    }
    D.ekipman.forEach(e => {
      if (e.tip === "ring") return;
      const G = merkezVeEksen(e.poligon), g = new T.Group();
      const W = G.uzun, Dp = G.kisa, H2 = e.h;
      if (e.tip === "kosu") {                       // koşu bandı
        kutu(g, W * 0.96, 0.16, Dp * 0.92, ekKoyu, 0, 0.10, 0);            // taban
        kutu(g, W * 0.62, 0.05, Dp * 0.70, mat("#0E1113", 0.95), -W * 0.14, 0.20, 0); // bant
        kutu(g, 0.08, H2 - 0.30, 0.08, ekMat,  W * 0.36, (H2 - 0.30) / 2 + 0.18,  Dp * 0.32);
        kutu(g, 0.08, H2 - 0.30, 0.08, ekMat,  W * 0.36, (H2 - 0.30) / 2 + 0.18, -Dp * 0.32);
        kutu(g, 0.16, 0.34, Dp * 0.82, ekMat,  W * 0.40, H2 - 0.16, 0);    // konsol
        kutu(g, 0.05, 0.05, Dp * 0.74, ekAks,  W * 0.20, H2 - 0.42, 0);    // tutamak
      } else if (e.tip === "bisiklet") {            // kondisyon bisikleti
        kutu(g, W * 0.92, 0.12, 0.14, ekKoyu, 0, 0.07, 0);
        kutu(g, 0.10, H2 * 0.55, 0.10, ekMat, -W * 0.18, H2 * 0.30, 0);
        kutu(g, 0.34, 0.10, 0.20, ekMat, -W * 0.18, H2 * 0.60, 0);         // sele
        kutu(g, 0.10, H2 * 0.78, 0.10, ekMat,  W * 0.26, H2 * 0.42, 0);
        kutu(g, 0.09, 0.26, Dp * 0.80, ekAks,  W * 0.26, H2 * 0.86, 0);    // gidon+konsol
        const vol = new T.Mesh(new T.CylinderGeometry(0.24, 0.24, 0.07, 20), ekAks);
        vol.rotation.z = Math.PI / 2; vol.position.set(W * 0.04, 0.34, 0);
        vol.castShadow = true; g.add(vol);                                  // volan
      } else if (e.tip === "raf") {                 // dambıl rafı — 2 kat
        kutu(g, W, 0.08, Dp, ekKoyu, 0, 0.12, 0);
        kutu(g, W, 0.07, Dp * 0.9, ekMat, 0, 0.42, 0.02);
        kutu(g, W, 0.07, Dp * 0.9, ekMat, 0, 0.80, -0.02);
        kutu(g, 0.07, H2, 0.07, ekMat, -W * 0.46, H2 / 2, 0);
        kutu(g, 0.07, H2, 0.07, ekMat,  W * 0.46, H2 / 2, 0);
        for (let k = 0; k < 6; k++) {               // dambıllar
          const d1 = new T.Mesh(new T.CylinderGeometry(0.085, 0.085, 0.34, 12), ekKoyu);
          d1.rotation.z = Math.PI / 2;
          d1.position.set(-W * 0.38 + k * (W * 0.152), 0.53 + (k % 2 ? 0.38 : 0), 0.02);
          d1.castShadow = true; g.add(d1);
        }
      } else if (e.tip === "kablo") {               // kablo çapraz / functional trainer
        kutu(g, W * 0.96, 0.14, Dp * 0.22, ekKoyu, 0, 0.07,  Dp * 0.36);
        kutu(g, W * 0.96, 0.14, Dp * 0.22, ekKoyu, 0, 0.07, -Dp * 0.36);
        [-1, 1].forEach(sx => {
          kutu(g, 0.14, H2, 0.14, ekMat, sx * W * 0.44, H2 / 2, 0);        // kule
          kutu(g, 0.30, H2 * 0.45, Dp * 0.26, ekKoyu, sx * W * 0.44, H2 * 0.26, 0); // ağırlık takozu
          const kol = new T.Mesh(new T.BoxGeometry(0.05, 0.05, Dp * 0.30), ekAks);
          kol.position.set(sx * W * 0.44, H2 - 0.12, Dp * 0.15); g.add(kol);
        });
        kutu(g, W * 0.88, 0.10, 0.10, ekMat, 0, H2 - 0.06, 0);             // üst kiriş
        kutu(g, 0.05, 0.05, Dp * 0.62, ekAks, 0, H2 - 0.30, 0);            // barfiks
      } else {                                      // çok fonksiyonlu kuvvet istasyonu
        kutu(g, W * 0.96, 0.14, Dp * 0.9, ekKoyu, 0, 0.07, 0);
        kutu(g, 0.13, H2, 0.13, ekMat, -W * 0.42, H2 / 2, 0);
        kutu(g, 0.13, H2, 0.13, ekMat,  W * 0.42, H2 / 2, 0);
        kutu(g, W * 0.90, 0.10, 0.10, ekMat, 0, H2 - 0.06, 0);
        kutu(g, W * 0.34, H2 * 0.52, Dp * 0.55, ekKoyu, W * 0.14, H2 * 0.30, 0); // ağırlık takozu
        kutu(g, W * 0.30, 0.09, Dp * 0.70, ekAks, -W * 0.22, 0.48, 0);     // oturma pedi
        kutu(g, 0.09, 0.46, Dp * 0.62, ekAks, -W * 0.36, 0.72, 0);         // sırt pedi
      }
      g.position.set(G.cx, 0.02, G.cy); g.rotation.y = G.ang; root.add(g);
    });
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
