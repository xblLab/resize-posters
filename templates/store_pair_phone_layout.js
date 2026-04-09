/**
 * 双屏上架模板（store_pair_left / store_pair_right）共用：
 * 机框 + 截屏 的尺寸、舞台内位置、3D 倾斜 —— 只改 STORE_PAIR_PHONE 一处即可。
 *
 * 也可在页面加载后执行：
 *   applyStorePairPhoneLayout(document.documentElement, { cropWidthPx: 820, rotateDeg: { z: 18 } });
 * URL 查询参数会叠加在默认值之上（见 applyStorePairPhoneLayout 文末说明）。
 */
(function (global) {
    /**
     * @typedef {Object} StorePairPhoneLayout
     * @property {{ x: number|string, y: number|string }} anchor
     *   虚拟舞台 2160×1920 内 .perspective-wrap 的定位（左上为原点）。
     *   数字会当作 px；字符串可写 '52%'、'1080px'。
     * @property {number} cropWidthPx 机框外接矩形宽度（.phone-crop），高度随设备宽高比。
     * @property {number} perspectivePx CSS perspective
     * @property {{ z: number, y: number, x: number }} rotateDeg 绕 Z/Y/X 轴旋转（度），顺序与 CSS 一致：Z → Y → X
     * @property {Object} deviceFrame 与 assets 中 PNG 配套的裁切与屏幕槽（换机框时主要改这里）
     * @property {number} deviceFrame.sourceW deviceFrame.sourceH 机框图源像素尺寸
     * @property {number} deviceFrame.frameOffsetX deviceFrame.frameOffsetY 机框图在图源中的左上偏移（与现 --phone-l/--phone-t 一致）
     * @property {Object} deviceFrame.screen
     * @property {number} deviceFrame.screen.leftPct topPct widthPct 屏幕区域相对机框的百分比
     * @property {number} deviceFrame.screen.heightPx 屏幕槽高度（px）
     * @property {number} deviceFrame.screen.slotTopAdjustPx 与 screen.top 叠加时的上移修正（px），对应原 calc 中的减数
     */

    /** @type {StorePairPhoneLayout} */
    var STORE_PAIR_PHONE = {
        anchor: { x: 1080, y: '52%' },
        cropWidthPx: 720,
        perspectivePx: 2200,
        rotateDeg: { z: 22, y: -12, x: 6 },
        deviceFrame: {
            sourceW: 4021,
            sourceH: 8281,
            frameOffsetX: 3000,
            frameOffsetY: 860,
            screen: {
                leftPct: 3.009,
                topPct: 5.579,
                widthPct: 92.99,
                heightPx: 1440,
                slotTopAdjustPx: 54,
            },
        },
    };

    function _asCssLen(v) {
        if (v === undefined || v === null) return '';
        if (typeof v === 'number' && Number.isFinite(v)) return v + 'px';
        return String(v);
    }

    function _deepMerge(base) {
        var rest = Array.prototype.slice.call(arguments, 1);
        var out = JSON.parse(JSON.stringify(base));
        for (var i = 0; i < rest.length; i++) {
            var patch = rest[i];
            if (!patch || typeof patch !== 'object') continue;
            for (var k in patch) {
                if (!Object.prototype.hasOwnProperty.call(patch, k)) continue;
                var pv = patch[k];
                if (
                    pv &&
                    typeof pv === 'object' &&
                    !Array.isArray(pv) &&
                    out[k] &&
                    typeof out[k] === 'object' &&
                    !Array.isArray(out[k])
                ) {
                    out[k] = _deepMerge(out[k], pv);
                } else {
                    out[k] = pv;
                }
            }
        }
        return out;
    }

    /**
     * 将布局写入 :root 的 CSS 变量（供模板样式使用）。
     * @param {HTMLElement} [root] 默认 document.documentElement
     * @param {Partial<StorePairPhoneLayout>} [overrides] 覆盖 STORE_PAIR_PHONE
     */
    function applyStorePairPhoneLayout(root, overrides) {
        var el = root || document.documentElement;
        var L = _deepMerge(STORE_PAIR_PHONE, overrides || {});
        var df = L.deviceFrame;
        var sc = df.screen;
        var s = el.style;

        s.setProperty('--phone-anchor-x', _asCssLen(L.anchor.x));
        s.setProperty('--phone-anchor-y', _asCssLen(L.anchor.y));
        s.setProperty('--phone-crop-width', String(L.cropWidthPx) + 'px');
        s.setProperty('--perspective', String(L.perspectivePx) + 'px');

        s.setProperty('--rz', L.rotateDeg.z + 'deg');
        s.setProperty('--ry', L.rotateDeg.y + 'deg');
        s.setProperty('--rx', L.rotateDeg.x + 'deg');

        s.setProperty('--phone-w', String(df.sourceW));
        s.setProperty('--phone-h', String(df.sourceH));
        s.setProperty('--phone-l', String(df.frameOffsetX));
        s.setProperty('--phone-t', String(df.frameOffsetY));

        s.setProperty('--screen-left', sc.leftPct + '%');
        s.setProperty('--screen-top', sc.topPct + '%');
        s.setProperty('--screen-width', sc.widthPct + '%');
        s.setProperty('--screen-slot-height', sc.heightPx + 'px');
        s.setProperty('--screen-slot-top-adjust', sc.slotTopAdjustPx + 'px');
    }

    /**
     * 从 URL 查询参数生成 overrides（可与 STORE_PAIR_PHONE 合并）。
     * 兼容原有：rotateZ, rotateY, rotateX, perspective
     * 新增：phoneWidth, anchorX, anchorY（anchor 可为 px 或带单位）
     */
    function storePairPhoneOverridesFromParams(params) {
        /** @type {Record<string, unknown>} */
        var o = {};

        function num(name) {
            var v = params.get(name);
            if (v === null || v === '') return undefined;
            var n = parseFloat(String(v).replace(/deg$/i, ''));
            return Number.isFinite(n) ? n : undefined;
        }

        var rz = num('rotateZ');
        var ry = num('rotateY');
        var rx = num('rotateX');
        if (rz !== undefined || ry !== undefined || rx !== undefined) {
            o.rotateDeg = {};
            if (rz !== undefined) o.rotateDeg.z = rz;
            if (ry !== undefined) o.rotateDeg.y = ry;
            if (rx !== undefined) o.rotateDeg.x = rx;
        }

        var persp = params.get('perspective');
        if (persp !== null && persp !== '') {
            o.perspectivePx = parseFloat(String(persp).replace(/px$/i, ''));
            if (!Number.isFinite(o.perspectivePx)) delete o.perspectivePx;
        }

        var pw = num('phoneWidth');
        if (pw !== undefined) o.cropWidthPx = pw;

        var ax = params.get('anchorX');
        if (ax !== null && ax !== '') {
            o.anchor = o.anchor || {};
            o.anchor.x = /%|px$/i.test(String(ax).trim()) ? String(ax).trim() : parseFloat(ax);
        }
        var ay = params.get('anchorY');
        if (ay !== null && ay !== '') {
            o.anchor = o.anchor || {};
            o.anchor.y = /%|px$/i.test(String(ay).trim()) ? String(ay).trim() : parseFloat(ay);
        }

        return o;
    }

    global.STORE_PAIR_PHONE = STORE_PAIR_PHONE;
    global.applyStorePairPhoneLayout = applyStorePairPhoneLayout;
    global.storePairPhoneOverridesFromParams = storePairPhoneOverridesFromParams;
})(typeof window !== 'undefined' ? window : globalThis);
