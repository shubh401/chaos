// Known Global Variables
(() => {
	let seenVars = new Set([
		"CreateMonitor",
		"LanguageDetector",
		"Summarizer",
		"Translator",
		"viewport",
		"CSSFunctionDeclarations",
		"CSSFunctionDescriptors",
		"CSSFunctionRule",
		"IntegrityViolationReportBody",
		"QuotaExceededError",
		"SpeechGrammar",
		"SpeechGrammarList",
		"SpeechRecognition",
		"SpeechRecognitionErrorEvent",
		"SpeechRecognitionEvent",
		"Viewport",
		"SparkMD5",
		"Observable",
		"Subscriber",
		"oncommand",
		"CommandEvent",
		"__playwright__binding__",
		"__pwInitScripts",
		"__dispatchErrorLog",
		"__exposedErrorLogger",
		"__exposedHookStateLogger",
		"Float16Array",
		"HTMLSelectedContentElement",
		"__dispatchPollData",
		"__Set",
		"WebTransportSendStream",
		"GamepadPose",
		"WebTransportReceiveStream",
		"Localization",
		"__ctx",
		"__canvas",
		"CSSPositionTryDescriptors",
		"PressureObserver",
		"PressureRecord",
		"dispatchKeyboardEvent",
		"textSelector",
		"mouseEventOnElement",
		"simulateScrollEvent",
		"simulateWheelEvent",
		"singleClick",
		"doubleClick",
		"elementTextSelector",
		"simulateInputEvent",
		"PageSwapEvent",
		"onpageswap",
		"ViewTransitionTypeSet",
		"WebSocketError",
		"WebSocketStream",
		"__fetch",
		"CSSScopeRule",
		"0",
		"1",
		"2",
		"Object",
		"Function",
		"Array",
		"Number",
		"parseFloat",
		"parseInt",
		"Infinity",
		"NaN",
		"__hookProperty",
		"parent_caller",
		"parent_caller_name",
		"parent_caller_string",
		"undefined",
		"Boolean",
		"String",
		"Symbol",
		"Date",
		"Promise",
		"RegExp",
		"Error",
		"seenVars",
		"AggregateError",
		"EvalError",
		"RangeError",
		"ReferenceError",
		"SyntaxError",
		"TypeError",
		"URIError",
		"globalThis",
		"JSON",
		"Math",
		"Intl",
		"ArrayBuffer",
		"Atomics",
		"Uint8Array",
		"Int8Array",
		"webSocket",
		"CookieDeprecationLabel",
		"CharacterBoundsUpdateEvent",
		"MediaStreamTrackVideoStats",
		"IdentityCredentialError",
		"NavigatorLogin",
		"CloseWatcher",
		"cdc_adoQpoasnfa76pfcZLmcfl_Array",
		"cdc_adoQpoasnfa76pfcZLmcfl_Object",
		"cdc_adoQpoasnfa76pfcZLmcfl_Promise",
		"cdc_adoQpoasnfa76pfcZLmcfl_Proxy",
		"cdc_adoQpoasnfa76pfcZLmcfl_Symbol",
		"cdc_adoQpoasnfa76pfcZLmcfl_JSON",
		"fence",
		"sizeToContent",
		"setResizable",
		"mozInnerScreenX",
		"mozInnerScreenY",
		"InstallTrigger",
		"onmozfullscreenchange",
		"onmozfullscreenerror",
		"onanimationcancel",
		"ongamepadconnected",
		"ongamepaddisconnected",
		"netscape",
		"InternalError",
		"SharedArrayBuffer",
		"CSS2Properties",
		"FileSystemEntry",
		"FileSystem",
		"CSSFontFeatureValuesRule",
		"PopupBlockedEvent",
		"MediaKeyError",
		"ScrollAreaEvent",
		"RTCRtpScriptTransform",
		"FileSystemDirectoryEntry",
		"PaintRequest",
		"MediaStreamTrackAudioSourceNode",
		"SpeechSynthesisVoice",
		"MouseScrollEvent",
		"CaretPosition",
		"FileSystemDirectoryReader",
		"FontFaceSet",
		"MediaCapabilitiesInfo",
		"CanvasCaptureMediaStream",
		"MediaRecorderErrorEvent",
		"FileSystemFileEntry",
		"PaintRequestList",
		"TimeEvent",
		"VTTRegion",
		"SpeechSynthesis",
		"Directory",
		"DOMRequest",
		"KeyEvent",
		"CSSMozDocumentRule",
		"NotifyPaintEvent",
		"onpaste",
		"oncut",
		"oncopy",
		"ondragexit",
		"sharedStorage",
		"Fence",
		"SharedStorage",
		"SharedStorageWorklet",
		"HTMLFencedFrameElement",
		"FencedFrameConfig",
		"__pollStorage",
		"sendData",
		"getIndexedDBData",
		"myVar",
		"Uint16Array",
		"Int16Array",
		"Uint32Array",
		"Int32Array",
		"Float32Array",
		"Float64Array",
		"Uint8ClampedArray",
		"BigUint64Array",
		"BigInt64Array",
		"DataView",
		"Map",
		"BigInt",
		"Set",
		"WeakMap",
		"WeakSet",
		"Proxy",
		"Reflect",
		"FinalizationRegistry",
		"WeakRef",
		"decodeURI",
		"decodeURIComponent",
		"encodeURI",
		"encodeURIComponent",
		"escape",
		"unescape",
		"eval",
		"isFinite",
		"isNaN",
		"console",
		"Option",
		"Image",
		"Audio",
		"webkitURL",
		"webkitRTCPeerConnection",
		"webkitMediaStream",
		"WebKitMutationObserver",
		"WebKitCSSMatrix",
		"XSLTProcessor",
		"XPathResult",
		"XPathExpression",
		"XPathEvaluator",
		"XMLSerializer",
		"XMLHttpRequestUpload",
		"XMLHttpRequestEventTarget",
		"XMLHttpRequest",
		"XMLDocument",
		"WritableStreamDefaultWriter",
		"WritableStreamDefaultController",
		"WritableStream",
		"Worker",
		"Window",
		"WheelEvent",
		"WebSocket",
		"WebGLVertexArrayObject",
		"WebGLUniformLocation",
		"WebGLTransformFeedback",
		"WebGLTexture",
		"WebGLSync",
		"WebGLShaderPrecisionFormat",
		"WebGLShader",
		"WebGLSampler",
		"WebGLRenderingContext",
		"WebGLRenderbuffer",
		"WebGLQuery",
		"WebGLProgram",
		"WebGLFramebuffer",
		"WebGLContextEvent",
		"WebGLBuffer",
		"WebGLActiveInfo",
		"WebGL2RenderingContext",
		"WaveShaperNode",
		"VisualViewport",
		"VirtualKeyboardGeometryChangeEvent",
		"ValidityState",
		"VTTCue",
		"UserActivation",
		"URLSearchParams",
		"URLPattern",
		"URL",
		"UIEvent",
		"TrustedTypePolicyFactory",
		"TrustedTypePolicy",
		"TrustedScriptURL",
		"TrustedScript",
		"TrustedHTML",
		"TreeWalker",
		"TransitionEvent",
		"TransformStreamDefaultController",
		"TransformStream",
		"TrackEvent",
		"TouchList",
		"TouchEvent",
		"Touch",
		"TimeRanges",
		"TextTrackList",
		"TextTrackCueList",
		"TextTrackCue",
		"TextTrack",
		"TextMetrics",
		"TextEvent",
		"TextEncoderStream",
		"TextEncoder",
		"TextDecoderStream",
		"TextDecoder",
		"Text",
		"TaskSignal",
		"TaskPriorityChangeEvent",
		"TaskController",
		"TaskAttributionTiming",
		"SyncManager",
		"SubmitEvent",
		"StyleSheetList",
		"StyleSheet",
		"StylePropertyMapReadOnly",
		"StylePropertyMap",
		"StorageEvent",
		"Storage",
		"StereoPannerNode",
		"StaticRange",
		"SourceBufferList",
		"SourceBuffer",
		"ShadowRoot",
		"Selection",
		"SecurityPolicyViolationEvent",
		"ScriptProcessorNode",
		"ScreenOrientation",
		"Screen",
		"Scheduling",
		"Scheduler",
		"SVGViewElement",
		"SVGUseElement",
		"SVGUnitTypes",
		"SVGTransformList",
		"SVGTransform",
		"SVGTitleElement",
		"SVGTextPositioningElement",
		"SVGTextPathElement",
		"SVGTextElement",
		"SVGTextContentElement",
		"SVGTSpanElement",
		"SVGSymbolElement",
		"SVGSwitchElement",
		"SVGStyleElement",
		"SVGStringList",
		"SVGStopElement",
		"SVGSetElement",
		"SVGScriptElement",
		"SVGSVGElement",
		"SVGRectElement",
		"SVGRect",
		"SVGRadialGradientElement",
		"SVGPreserveAspectRatio",
		"SVGPolylineElement",
		"SVGPolygonElement",
		"SVGPointList",
		"SVGPoint",
		"SVGPatternElement",
		"SVGPathElement",
		"SVGNumberList",
		"SVGNumber",
		"SVGMetadataElement",
		"SVGMatrix",
		"SVGMaskElement",
		"SVGMarkerElement",
		"SVGMPathElement",
		"SVGLinearGradientElement",
		"SVGLineElement",
		"SVGLengthList",
		"SVGLength",
		"SVGImageElement",
		"SVGGraphicsElement",
		"SVGGradientElement",
		"SVGGeometryElement",
		"SVGGElement",
		"SVGForeignObjectElement",
		"SVGFilterElement",
		"SVGFETurbulenceElement",
		"SVGFETileElement",
		"SVGFESpotLightElement",
		"SVGFESpecularLightingElement",
		"SVGFEPointLightElement",
		"SVGFEOffsetElement",
		"SVGFEMorphologyElement",
		"SVGFEMergeNodeElement",
		"SVGFEMergeElement",
		"SVGFEImageElement",
		"SVGFEGaussianBlurElement",
		"SVGFEFuncRElement",
		"SVGFEFuncGElement",
		"SVGFEFuncBElement",
		"SVGFEFuncAElement",
		"SVGFEFloodElement",
		"SVGFEDropShadowElement",
		"SVGFEDistantLightElement",
		"SVGFEDisplacementMapElement",
		"SVGFEDiffuseLightingElement",
		"SVGFEConvolveMatrixElement",
		"SVGFECompositeElement",
		"SVGFEComponentTransferElement",
		"SVGFEColorMatrixElement",
		"SVGFEBlendElement",
		"SVGEllipseElement",
		"SVGElement",
		"SVGDescElement",
		"SVGDefsElement",
		"SVGComponentTransferFunctionElement",
		"SVGClipPathElement",
		"SVGCircleElement",
		"SVGAnimationElement",
		"SVGAnimatedTransformList",
		"SVGAnimatedString",
		"SVGAnimatedRect",
		"SVGAnimatedPreserveAspectRatio",
		"SVGAnimatedNumberList",
		"SVGAnimatedNumber",
		"SVGAnimatedLengthList",
		"SVGAnimatedLength",
		"SVGAnimatedInteger",
		"SVGAnimatedEnumeration",
		"SVGAnimatedBoolean",
		"SVGAnimatedAngle",
		"SVGAnimateTransformElement",
		"SVGAnimateMotionElement",
		"SVGAnimateElement",
		"SVGAngle",
		"SVGAElement",
		"Response",
		"ResizeObserverSize",
		"ResizeObserverEntry",
		"ResizeObserver",
		"Request",
		"ReportingObserver",
		"ReadableStreamDefaultReader",
		"ReadableStreamDefaultController",
		"ReadableStreamBYOBRequest",
		"ReadableStreamBYOBReader",
		"ReadableStream",
		"ReadableByteStreamController",
		"Range",
		"RadioNodeList",
		"RTCTrackEvent",
		"RTCStatsReport",
		"RTCSessionDescription",
		"RTCSctpTransport",
		"RTCRtpTransceiver",
		"RTCRtpSender",
		"RTCRtpReceiver",
		"RTCPeerConnectionIceEvent",
		"RTCPeerConnectionIceErrorEvent",
		"RTCPeerConnection",
		"RTCIceTransport",
		"RTCIceCandidate",
		"RTCErrorEvent",
		"RTCError",
		"RTCEncodedVideoFrame",
		"RTCEncodedAudioFrame",
		"RTCDtlsTransport",
		"RTCDataChannelEvent",
		"RTCDataChannel",
		"RTCDTMFToneChangeEvent",
		"RTCDTMFSender",
		"RTCCertificate",
		"PromiseRejectionEvent",
		"ProgressEvent",
		"Profiler",
		"ProcessingInstruction",
		"PopStateEvent",
		"PointerEvent",
		"PluginArray",
		"Plugin",
		"PictureInPictureWindow",
		"PictureInPictureEvent",
		"PeriodicWave",
		"PerformanceTiming",
		"PerformanceServerTiming",
		"PerformanceResourceTiming",
		"PerformancePaintTiming",
		"PerformanceObserverEntryList",
		"PerformanceObserver",
		"PerformanceNavigationTiming",
		"PerformanceNavigation",
		"PerformanceMeasure",
		"PerformanceMark",
		"PerformanceLongTaskTiming",
		"PerformanceEventTiming",
		"PerformanceEntry",
		"PerformanceElementTiming",
		"Performance",
		"Path2D",
		"PannerNode",
		"PageTransitionEvent",
		"OverconstrainedError",
		"OscillatorNode",
		"Iterator",
		"EditContext",
		"TextFormat",
		"TextFormatUpdateEvent",
		"TextUpdateEvent",
		"FetchLaterResult",
		"NotRestoredReasonDetails",
		"NotRestoredReasons",
		"ProtectedAudience",
		"StorageBucket",
		"StorageBucketManager",
		"fetchLater",
		"onpagereveal",
		"NavigationActivation",
		"PageRevealEvent",
		"PerformanceLongAnimationFrameTiming",
		"PerformanceScriptTiming",
		"OffscreenCanvasRenderingContext2D",
		"OffscreenCanvas",
		"OfflineAudioContext",
		"OfflineAudioCompletionEvent",
		"NodeList",
		"NodeIterator",
		"NodeFilter",
		"Node",
		"NetworkInformation",
		"Navigator",
		"NavigationTransition",
		"NavigationHistoryEntry",
		"NavigationDestination",
		"NavigationCurrentEntryChangeEvent",
		"Navigation",
		"NavigateEvent",
		"NamedNodeMap",
		"MutationRecord",
		"MutationObserver",
		"MouseEvent",
		"MimeTypeArray",
		"MimeType",
		"MessagePort",
		"MessageEvent",
		"MessageChannel",
		"MediaStreamTrackProcessor",
		"MediaStreamTrackGenerator",
		"MediaStreamTrackEvent",
		"MediaStreamTrack",
		"MediaStreamEvent",
		"MediaStreamAudioSourceNode",
		"MediaStreamAudioDestinationNode",
		"MediaStream",
		"MediaSourceHandle",
		"MediaSource",
		"MediaRecorder",
		"MediaQueryListEvent",
		"MediaQueryList",
		"MediaList",
		"MediaError",
		"MediaEncryptedEvent",
		"MediaElementAudioSourceNode",
		"MediaCapabilities",
		"MathMLElement",
		"Location",
		"LayoutShiftAttribution",
		"LayoutShift",
		"LargestContentfulPaint",
		"KeyframeEffect",
		"KeyboardEvent",
		"IntersectionObserverEntry",
		"IntersectionObserver",
		"InputEvent",
		"InputDeviceInfo",
		"InputDeviceCapabilities",
		"ImageData",
		"ImageCapture",
		"ImageBitmapRenderingContext",
		"ImageBitmap",
		"IdleDeadline",
		"IIRFilterNode",
		"IDBVersionChangeEvent",
		"IDBTransaction",
		"IDBRequest",
		"IDBOpenDBRequest",
		"IDBObjectStore",
		"IDBKeyRange",
		"IDBIndex",
		"IDBFactory",
		"IDBDatabase",
		"IDBCursorWithValue",
		"IDBCursor",
		"History",
		"Headers",
		"HashChangeEvent",
		"HTMLVideoElement",
		"HTMLUnknownElement",
		"HTMLUListElement",
		"HTMLTrackElement",
		"HTMLTitleElement",
		"HTMLTimeElement",
		"HTMLTextAreaElement",
		"HTMLTemplateElement",
		"HTMLTableSectionElement",
		"HTMLTableRowElement",
		"HTMLTableElement",
		"HTMLTableColElement",
		"HTMLTableCellElement",
		"HTMLTableCaptionElement",
		"HTMLStyleElement",
		"HTMLSpanElement",
		"HTMLSourceElement",
		"HTMLSlotElement",
		"HTMLSelectElement",
		"HTMLScriptElement",
		"HTMLQuoteElement",
		"HTMLProgressElement",
		"HTMLPreElement",
		"HTMLPictureElement",
		"HTMLParamElement",
		"HTMLParagraphElement",
		"HTMLOutputElement",
		"HTMLOptionsCollection",
		"HTMLOptionElement",
		"HTMLOptGroupElement",
		"HTMLObjectElement",
		"HTMLOListElement",
		"HTMLModElement",
		"HTMLMeterElement",
		"HTMLMetaElement",
		"HTMLMenuElement",
		"HTMLMediaElement",
		"HTMLMarqueeElement",
		"HTMLMapElement",
		"HTMLLinkElement",
		"HTMLLegendElement",
		"HTMLLabelElement",
		"HTMLLIElement",
		"HTMLInputElement",
		"HTMLImageElement",
		"HTMLIFrameElement",
		"HTMLHtmlElement",
		"HTMLHeadingElement",
		"HTMLHeadElement",
		"HTMLHRElement",
		"HTMLFrameSetElement",
		"HTMLFrameElement",
		"HTMLFormElement",
		"HTMLFormControlsCollection",
		"HTMLFontElement",
		"HTMLFieldSetElement",
		"HTMLEmbedElement",
		"HTMLElement",
		"HTMLDocument",
		"HTMLDivElement",
		"HTMLDirectoryElement",
		"HTMLDialogElement",
		"HTMLDetailsElement",
		"HTMLDataListElement",
		"HTMLDataElement",
		"HTMLDListElement",
		"HTMLCollection",
		"HTMLCanvasElement",
		"HTMLButtonElement",
		"HTMLBodyElement",
		"HTMLBaseElement",
		"HTMLBRElement",
		"HTMLAudioElement",
		"HTMLAreaElement",
		"HTMLAnchorElement",
		"HTMLAllCollection",
		"GeolocationPositionError",
		"GeolocationPosition",
		"GeolocationCoordinates",
		"Geolocation",
		"GamepadHapticActuator",
		"GamepadEvent",
		"GamepadButton",
		"Gamepad",
		"GainNode",
		"FormDataEvent",
		"FormData",
		"FontFaceSetLoadEvent",
		"FontFace",
		"FocusEvent",
		"FileReader",
		"FileList",
		"File",
		"FeaturePolicy",
		"External",
		"EventTarget",
		"EventSource",
		"EventCounts",
		"Event",
		"ErrorEvent",
		"ElementInternals",
		"Element",
		"DynamicsCompressorNode",
		"DragEvent",
		"DocumentType",
		"DocumentFragment",
		"Document",
		"DelayNode",
		"DecompressionStream",
		"DataTransferItemList",
		"DataTransferItem",
		"DataTransfer",
		"DOMTokenList",
		"DOMStringMap",
		"DOMStringList",
		"DOMRectReadOnly",
		"DOMRectList",
		"DOMRect",
		"DOMQuad",
		"DOMPointReadOnly",
		"DOMPoint",
		"DOMParser",
		"DOMMatrixReadOnly",
		"DOMMatrix",
		"DOMImplementation",
		"DOMException",
		"DOMError",
		"CustomStateSet",
		"CustomEvent",
		"CustomElementRegistry",
		"Crypto",
		"CountQueuingStrategy",
		"ConvolverNode",
		"ConstantSourceNode",
		"CompressionStream",
		"CompositionEvent",
		"Comment",
		"CloseEvent",
		"ClipboardEvent",
		"CharacterData",
		"ChannelSplitterNode",
		"ChannelMergerNode",
		"CanvasRenderingContext2D",
		"CanvasPattern",
		"CanvasGradient",
		"CanvasCaptureMediaStreamTrack",
		"CSSVariableReferenceValue",
		"CSSPositionTryRule",
		"MediaStreamTrackAudioStats",
		"decode_utf8",
		"setTextP",
		"CSSUnparsedValue",
		"CSSUnitValue",
		"CSSTranslate",
		"CSSTransformValue",
		"CSSTransformComponent",
		"CSSSupportsRule",
		"CSSStyleValue",
		"CSSStyleSheet",
		"CSSStyleRule",
		"CSSStyleDeclaration",
		"CSSSkewY",
		"CSSSkewX",
		"CSSSkew",
		"CSSScale",
		"CSSRuleList",
		"CSSRule",
		"CSSRotate",
		"CSSPropertyRule",
		"CSSPositionValue",
		"CSSPerspective",
		"CSSPageRule",
		"CSSNumericValue",
		"CSSNumericArray",
		"CSSNamespaceRule",
		"CSSMediaRule",
		"CSSMatrixComponent",
		"CSSMathValue",
		"CSSMathSum",
		"CSSMathProduct",
		"CSSMathNegate",
		"CSSMathMin",
		"CSSMathMax",
		"CSSMathInvert",
		"CSSMathClamp",
		"CSSLayerStatementRule",
		"CSSLayerBlockRule",
		"CSSKeywordValue",
		"CSSKeyframesRule",
		"CSSKeyframeRule",
		"CSSImportRule",
		"CSSImageValue",
		"CSSGroupingRule",
		"CSSFontPaletteValuesRule",
		"CSSFontFaceRule",
		"CSSCounterStyleRule",
		"CSSContainerRule",
		"CSSConditionRule",
		"CSS",
		"CDATASection",
		"ByteLengthQueuingStrategy",
		"BroadcastChannel",
		"BlobEvent",
		"Blob",
		"BiquadFilterNode",
		"BeforeUnloadEvent",
		"BeforeInstallPromptEvent",
		"BaseAudioContext",
		"BarProp",
		"AudioWorkletNode",
		"AudioSinkInfo",
		"AudioScheduledSourceNode",
		"AudioProcessingEvent",
		"AudioParamMap",
		"AudioParam",
		"AudioNode",
		"AudioListener",
		"AudioDestinationNode",
		"AudioContext",
		"AudioBufferSourceNode",
		"AudioBuffer",
		"Attr",
		"AnimationEvent",
		"AnimationEffect",
		"Animation",
		"AnalyserNode",
		"AbstractRange",
		"AbortSignal",
		"AbortController",
		"window",
		"self",
		"document",
		"name",
		"location",
		"customElements",
		"history",
		"navigation",
		"locationbar",
		"menubar",
		"personalbar",
		"scrollbars",
		"statusbar",
		"toolbar",
		"status",
		"closed",
		"frames",
		"length",
		"top",
		"opener",
		"parent",
		"frameElement",
		"navigator",
		"origin",
		"external",
		"screen",
		"innerWidth",
		"innerHeight",
		"scrollX",
		"pageXOffset",
		"scrollY",
		"pageYOffset",
		"visualViewport",
		"screenX",
		"screenY",
		"outerWidth",
		"outerHeight",
		"devicePixelRatio",
		"event",
		"clientInformation",
		"offscreenBuffering",
		"screenLeft",
		"screenTop",
		"styleMedia",
		"onsearch",
		"isSecureContext",
		"trustedTypes",
		"performance",
		"onappinstalled",
		"onbeforeinstallprompt",
		"crypto",
		"indexedDB",
		"sessionStorage",
		"localStorage",
		"onbeforexrselect",
		"onabort",
		"onbeforeinput",
		"onblur",
		"oncancel",
		"oncanplay",
		"oncanplaythrough",
		"onchange",
		"onclick",
		"onclose",
		"oncontextlost",
		"oncontextmenu",
		"oncontextrestored",
		"oncuechange",
		"ondblclick",
		"ondrag",
		"ondragend",
		"ondragenter",
		"ondragleave",
		"ondragover",
		"ondragstart",
		"ondrop",
		"ondurationchange",
		"onemptied",
		"onended",
		"onerror",
		"onfocus",
		"onformdata",
		"oninput",
		"oninvalid",
		"onkeydown",
		"onkeypress",
		"onkeyup",
		"onload",
		"onloadeddata",
		"onloadedmetadata",
		"onloadstart",
		"onmousedown",
		"onmouseenter",
		"onmouseleave",
		"onmousemove",
		"onmouseout",
		"onmouseover",
		"onmouseup",
		"onmousewheel",
		"onpause",
		"onplay",
		"onplaying",
		"onprogress",
		"onratechange",
		"onreset",
		"onresize",
		"onscroll",
		"onsecuritypolicyviolation",
		"onseeked",
		"onseeking",
		"onselect",
		"onslotchange",
		"onstalled",
		"onsubmit",
		"onsuspend",
		"ontimeupdate",
		"ontoggle",
		"onvolumechange",
		"onwaiting",
		"onwebkitanimationend",
		"onwebkitanimationiteration",
		"onwebkitanimationstart",
		"onwebkittransitionend",
		"onwheel",
		"onauxclick",
		"ongotpointercapture",
		"onlostpointercapture",
		"onpointerdown",
		"onpointermove",
		"onpointerrawupdate",
		"onpointerup",
		"onpointercancel",
		"onpointerover",
		"onpointerout",
		"onpointerenter",
		"onpointerleave",
		"onselectstart",
		"onselectionchange",
		"onanimationend",
		"onanimationiteration",
		"onanimationstart",
		"ontransitionrun",
		"ontransitionstart",
		"ontransitionend",
		"ontransitioncancel",
		"onafterprint",
		"onbeforeprint",
		"onbeforeunload",
		"onhashchange",
		"onlanguagechange",
		"onmessage",
		"onmessageerror",
		"onoffline",
		"ononline",
		"onpagehide",
		"onpageshow",
		"onpopstate",
		"onrejectionhandled",
		"onstorage",
		"onunhandledrejection",
		"onunload",
		"crossOriginIsolated",
		"scheduler",
		"alert",
		"atob",
		"blur",
		"btoa",
		"cancelAnimationFrame",
		"cancelIdleCallback",
		"captureEvents",
		"clearInterval",
		"clearTimeout",
		"close",
		"confirm",
		"createImageBitmap",
		"fetch",
		"find",
		"focus",
		"getComputedStyle",
		"getSelection",
		"matchMedia",
		"moveBy",
		"moveTo",
		"open",
		"postMessage",
		"print",
		"prompt",
		"queueMicrotask",
		"releaseEvents",
		"reportError",
		"requestAnimationFrame",
		"requestIdleCallback",
		"resizeBy",
		"resizeTo",
		"scroll",
		"scrollBy",
		"scrollTo",
		"setInterval",
		"setTimeout",
		"stop",
		"structuredClone",
		"webkitCancelAnimationFrame",
		"webkitRequestAnimationFrame",
		"chrome",
		"WebAssembly",
		"caches",
		"cookieStore",
		"ondevicemotion",
		"ondeviceorientation",
		"ondeviceorientationabsolute",
		"launchQueue",
		"documentPictureInPicture",
		"onbeforematch",
		"onbeforetoggle",
		"AbsoluteOrientationSensor",
		"Accelerometer",
		"AudioWorklet",
		"BatteryManager",
		"Cache",
		"CacheStorage",
		"Clipboard",
		"ClipboardItem",
		"CookieChangeEvent",
		"CookieStore",
		"CookieStoreManager",
		"Credential",
		"CredentialsContainer",
		"CryptoKey",
		"DeviceMotionEvent",
		"DeviceMotionEventAcceleration",
		"DeviceMotionEventRotationRate",
		"DeviceOrientationEvent",
		"FederatedCredential",
		"GravitySensor",
		"Gyroscope",
		"Keyboard",
		"KeyboardLayoutMap",
		"LinearAccelerationSensor",
		"Lock",
		"LockManager",
		"MIDIAccess",
		"MIDIConnectionEvent",
		"MIDIInput",
		"MIDIInputMap",
		"MIDIMessageEvent",
		"MIDIOutput",
		"MIDIOutputMap",
		"MIDIPort",
		"MediaDeviceInfo",
		"MediaDevices",
		"MediaKeyMessageEvent",
		"MediaKeySession",
		"MediaKeyStatusMap",
		"MediaKeySystemAccess",
		"MediaKeys",
		"NavigationPreloadManager",
		"NavigatorManagedData",
		"OrientationSensor",
		"PasswordCredential",
		"RelativeOrientationSensor",
		"Sanitizer",
		"ScreenDetailed",
		"ScreenDetails",
		"Sensor",
		"SensorErrorEvent",
		"ServiceWorker",
		"ServiceWorkerContainer",
		"ServiceWorkerRegistration",
		"StorageManager",
		"SubtleCrypto",
		"VirtualKeyboard",
		"WebTransport",
		"WebTransportBidirectionalStream",
		"WebTransportDatagramDuplexStream",
		"WebTransportError",
		"Worklet",
		"XRDOMOverlayState",
		"XRLayer",
		"XRWebGLBinding",
		"AudioData",
		"EncodedAudioChunk",
		"EncodedVideoChunk",
		"ImageTrack",
		"ImageTrackList",
		"VideoColorSpace",
		"VideoFrame",
		"AudioDecoder",
		"AudioEncoder",
		"ImageDecoder",
		"VideoDecoder",
		"VideoEncoder",
		"AuthenticatorAssertionResponse",
		"AuthenticatorAttestationResponse",
		"AuthenticatorResponse",
		"PublicKeyCredential",
		"BarcodeDetector",
		"Bluetooth",
		"BluetoothCharacteristicProperties",
		"BluetoothDevice",
		"BluetoothRemoteGATTCharacteristic",
		"BluetoothRemoteGATTDescriptor",
		"BluetoothRemoteGATTServer",
		"BluetoothRemoteGATTService",
		"CaptureController",
		"DocumentPictureInPicture",
		"EyeDropper",
		"FileSystemDirectoryHandle",
		"FileSystemFileHandle",
		"FileSystemHandle",
		"FileSystemWritableFileStream",
		"FontData",
		"FragmentDirective",
		"GPU",
		"GPUAdapter",
		"GPUAdapterInfo",
		"GPUBindGroup",
		"GPUBindGroupLayout",
		"GPUBuffer",
		"GPUBufferUsage",
		"GPUCanvasContext",
		"GPUColorWrite",
		"GPUCommandBuffer",
		"GPUCommandEncoder",
		"GPUCompilationInfo",
		"GPUCompilationMessage",
		"GPUComputePassEncoder",
		"GPUComputePipeline",
		"GPUDevice",
		"GPUDeviceLostInfo",
		"GPUError",
		"GPUExternalTexture",
		"GPUInternalError",
		"GPUMapMode",
		"GPUOutOfMemoryError",
		"GPUPipelineError",
		"GPUPipelineLayout",
		"GPUQuerySet",
		"GPUQueue",
		"GPURenderBundle",
		"GPURenderBundleEncoder",
		"GPURenderPassEncoder",
		"GPURenderPipeline",
		"GPUSampler",
		"GPUShaderModule",
		"GPUShaderStage",
		"GPUSupportedFeatures",
		"GPUSupportedLimits",
		"GPUTexture",
		"GPUTextureUsage",
		"GPUTextureView",
		"GPUUncapturedErrorEvent",
		"GPUValidationError",
		"WGSLLanguageFeatures",
		"HID",
		"HIDConnectionEvent",
		"HIDDevice",
		"HIDInputReportEvent",
		"IdentityCredential",
		"IdentityProvider",
		"IdleDetector",
		"LaunchParams",
		"LaunchQueue",
		"OTPCredential",
		"PaymentAddress",
		"PaymentRequest",
		"PaymentResponse",
		"PaymentMethodChangeEvent",
		"Presentation",
		"PresentationAvailability",
		"PresentationConnection",
		"PresentationConnectionAvailableEvent",
		"PresentationConnectionCloseEvent",
		"PresentationConnectionList",
		"PresentationReceiver",
		"PresentationRequest",
		"Serial",
		"SerialPort",
		"ToggleEvent",
		"USB",
		"USBAlternateInterface",
		"USBConfiguration",
		"USBConnectionEvent",
		"USBDevice",
		"USBEndpoint",
		"USBInTransferResult",
		"USBInterface",
		"USBIsochronousInTransferPacket",
		"USBIsochronousInTransferResult",
		"USBIsochronousOutTransferPacket",
		"USBIsochronousOutTransferResult",
		"USBOutTransferResult",
		"WakeLock",
		"WakeLockSentinel",
		"WindowControlsOverlay",
		"WindowControlsOverlayGeometryChangeEvent",
		"XRAnchor",
		"XRAnchorSet",
		"XRBoundedReferenceSpace",
		"XRCPUDepthInformation",
		"XRCamera",
		"XRDepthInformation",
		"XRFrame",
		"XRHitTestResult",
		"XRHitTestSource",
		"XRInputSource",
		"XRInputSourceArray",
		"XRInputSourceEvent",
		"XRInputSourcesChangeEvent",
		"XRLightEstimate",
		"XRLightProbe",
		"XRPose",
		"XRRay",
		"XRReferenceSpace",
		"XRReferenceSpaceEvent",
		"XRRenderState",
		"XRRigidTransform",
		"XRSession",
		"XRSessionEvent",
		"XRSpace",
		"XRSystem",
		"XRTransientInputHitTestResult",
		"XRTransientInputHitTestSource",
		"XRView",
		"XRViewerPose",
		"XRViewport",
		"XRWebGLDepthInformation",
		"XRWebGLLayer",
		"getScreenDetails",
		"openDatabase",
		"queryLocalFonts",
		"showDirectoryPicker",
		"showOpenFilePicker",
		"showSaveFilePicker",
		"originAgentCluster",
		"credentialless",
		"speechSynthesis",
		"oncontentvisibilityautostatechange",
		"onscrollend",
		"AnimationPlaybackEvent",
		"AnimationTimeline",
		"CSSAnimation",
		"CSSTransition",
		"DocumentTimeline",
		"BackgroundFetchManager",
		"BackgroundFetchRecord",
		"BackgroundFetchRegistration",
		"BluetoothUUID",
		"BrowserCaptureMediaStreamTrack",
		"CropTarget",
		"CSSStartingStyleRule",
		"ContentVisibilityAutoStateChangeEvent",
		"DelegatedInkTrailPresenter",
		"Ink",
		"DocumentPictureInPictureEvent",
		"Highlight",
		"HighlightRegistry",
		"MediaMetadata",
		"MediaSession",
		"MutationEvent",
		"NavigatorUAData",
		"Notification",
		"PaymentManager",
		"PaymentRequestUpdateEvent",
		"PeriodicSyncManager",
		"PermissionStatus",
		"Permissions",
		"PushManager",
		"PushSubscription",
		"PushSubscriptionOptions",
		"RemotePlayback",
		"ScrollTimeline",
		"ViewTimeline",
		"SharedWorker",
		"SpeechSynthesisErrorEvent",
		"SpeechSynthesisEvent",
		"SpeechSynthesisUtterance",
		"VideoPlaybackQuality",
		"ViewTransition",
		"VisibilityStateEntry",
		"webkitSpeechGrammar",
		"webkitSpeechGrammarList",
		"webkitSpeechRecognition",
		"webkitSpeechRecognitionError",
		"webkitSpeechRecognitionEvent",
		"webkitRequestFileSystem",
		"webkitResolveLocalFileSystemURL",
		"extensionId",
		"__ls",
		"__ss",
		"__setTimeout",
		"__stringify",
		"__addEventListener",
		"__cookieGetter",
		"getCircularReplacer",
		"__hookProperty",
		"defaultStatus",
		"fullScreen",
		"orientation",
		"scrollMaxX",
		"scrollMaxY",
		"back",
		"clearImmediate",
		"convertPointFromNodeToPage",
		"dump",
		"forward",
		"getDefaultComputedStyle",
		"requestFileSystem",
		"scrollByLines",
		"scrollByPages",
		"setImmediate",
		"showModalDialog",
		"updateCommands",
		"webkitConvertPointFromPageToNode",
		"callerName",
		"dir",
		"dirxml",
		"profile",
		"profileEnd",
		"clear",
		"table",
		"keys",
		"values",
		"debug",
		"undebug",
		"monitor",
		"unmonitor",
		"inspect",
		"copy",
		"queryObjects",
		"$_",
		"$0",
		"$1",
		"$2",
		"$3",
		"$4",
		"getEventListeners",
		"getAccessibleName",
		"getAccessibleRole",
		"monitorEvents",
		"unmonitorEvents",
		"$",
		"ctrlKey",
		"altKey",
		"shiftKey",
		"$$",
		"$x",
		"__getCircularReplacer",
		"sendInterceptedData",
		"myExtensionId",
		"myDataset",
		"myScriptName",
		"sendInterceptedData",
		"sendHookData",
		"CSPViolationReportBody",
		"XRJointPose",
		"XRHand",
		"__dispatchHookData",
		"__escape",
		"CSSViewTransitionRule",
		"ChapterInformation",
		"FileSystemObserver",
		"__encodeURIComponent",
		"CSSMarginRule",
		"ReportBody",
		"api_cnt",
		"SharedStorageModifierMethod",
		"DisposableStack",
		"__atob",
		"XRJointSpace",
		"AICreateMonitor",
		"__parseInt",
		"SharedStorageDeleteMethod",
		"counter",
		"__btoa",
		"WebGLObject",
		"DevicePosture",
		"SharedStorageClearMethod",
		"description",
		"CryptoJS",
		"CSSNestedDeclarations",
		"AsyncDisposableStack",
		"RestrictionTarget",
		"SnapEvent",
		"onscrollsnapchanging",
		"SuppressedError",
		"SharedStorageAppendMethod",
		"onscrollsnapchange",
		"SharedStorageSetMethod",
		"__unescape",
		"__dispatchEvent",
		"alinkColor",
		"bgColor",
		"characterSet",
		"childElementCount",
		"compatMode",
		"contentType",
		"cookie",
		"defaultView",
		"designMode",
		"dir",
		"domain",
		"fragmentDirective",
		"fgColor",
		"fullscreen",
		"fullscreenEnabled",
		"hidden",
		"lastModified",
		"lastStyleSheetSet",
		"linkColor",
		"preferredStyleSheetSet",
		"referrer",
		"title",
		"visibilityState",
		"URL",
	]);
})();

// Helper APIs & Methods
(() => {
	// API copies
	WeakSet.prototype.__add = WeakSet.prototype.add;
	WeakSet.prototype.__has = WeakSet.prototype.has;
	Set.prototype.__add = Set.prototype.add;
	Set.prototype.__has = Set.prototype.has;
	Map.prototype.__set = Map.prototype.set;
	Map.prototype.__get = Map.prototype.get;
	window.api_cnt = new Map();

	window.__ls = window.localStorage;
	window.__ss = window.sessionStorage;
	window.__setTimeout = window.setTimeout;
	console.__error = console.error;

	window.__stringify = JSON.stringify;
	Array.__from = Array.from;
	Array.prototype.__join = Array.prototype.join;
	Array.prototype.__toString = Array.prototype.toString;
	Array.prototype.__shift = Array.prototype.shift;
	Array.prototype.__splice = Array.prototype.splice;
	Array.prototype.__subarray = Array.prototype.subarray;
	Number.prototype.__toString = Number.prototype.toString;
	NodeList.prototype.__forEach = NodeList.prototype.forEach;
	Object.prototype.__toString = Object.prototype.toString;
	String.prototype.__split = String.prototype.split;
	String.prototype.__slice = String.prototype.slice;
	String.prototype.__toString = String.prototype.toString;
	RegExp.prototype.__toString = RegExp.prototype.toString;
	BigInt.prototype.__toString = BigInt.prototype.toString;
	Symbol.prototype.__toString = Symbol.prototype.toString;
	Boolean.prototype.__toString = Boolean.prototype.toString;
	Function.prototype.__bind = Function.prototype.bind;
	Function.prototype.__apply = Function.prototype.apply;
	Function.prototype.__toString = Function.prototype.toString;
	Element.prototype.__removeAttribute = Element.prototype.removeAttribute;
	window.__parseInt = window.parseInt;
	window.__atob = window.atob;
	window.__btoa = window.btoa;
	window.__escape = window.escape;

	__unescape = window.unescape;
	__encodeURIComponent = window.encodeURIComponent;
	Document.prototype.__createRange = Document.prototype.createRange;

	Object.__defineProperty = Object.defineProperty;
	Object.__create = Object.create;
	String.prototype.__startsWith = String.prototype.startsWith;
	String.prototype.__indexOf = String.prototype.indexOf;
	String.prototype.__charCodeAt = String.prototype.charCodeAt;
	String.prototype.__substr = String.prototype.substr;
	String.prototype.__substring = String.prototype.substring;

	IDBFactory.prototype.__open = IDBFactory.prototype.open;
	IDBFactory.prototype.__databases = IDBFactory.prototype.databases;
	IDBDatabase.prototype.__transaction = IDBDatabase.prototype.transaction;
	IDBTransaction.prototype.__objectStore =
		IDBTransaction.prototype.objectStore;
	IDBObjectStore.prototype.__openCursor =
		IDBObjectStore.prototype.openCursor;
	IDBCursor.prototype.__continue = IDBCursor.prototype.continue;
	Array.__isArray = Array.isArray;
	Array.prototype.__push = Array.prototype.push;
	Array.prototype.__includes = Array.prototype.includes;
	String.prototype.__includes = String.prototype.includes;
	Array.prototype.__forEach = Array.prototype.forEach;
	Object.prototype.___lookupGetter___ = Object.prototype.__lookupGetter__;
	Object.prototype.___lookupSetter___ = Object.prototype.__lookupSetter__;
	Object.__getOwnPropertyNames = Object.getOwnPropertyNames;
	Object.__keys = Object.keys;
	window.__addEventListener = window.addEventListener;
	document.__addEventListener = document.addEventListener;
	document.__dispatchEvent = document.dispatchEvent;
	window.__cookieGetter = document
		.___lookupGetter___("cookie")
		.__bind(document);
	window.__fetch = window.fetch;
	console.__log = console.log;
	Math.__min = Math.min;
	Math.__max = Math.max;
	Math.__ceil = Math.ceil;
	Math.__floor = Math.floor;
	Math.__random = Math.random;
	window.prompt = function () { };
	window.alert = function () { };
	Array.prototype.__slice = Array.prototype.slice;
	Object.prototype.__hasOwnProperty = Object.prototype.hasOwnProperty;
	EventTarget.prototype.__dispatchEvent =
		EventTarget.prototype.dispatchEvent;
	Document.prototype.__getElementById = Document.prototype.getElementById;
	Element.prototype.__addEventListener = Element.prototype.addEventListener;
	Element.prototype.__getBoundingClientRect =
		Element.prototype.getBoundingClientRect;
	RegExp.prototype.__test = RegExp.prototype.test;

	// Smart JSON-ifier
	window.__getCircularReplacer = function () {
		const ancestors = new WeakSet();
		return function (key, value) {
			if (value == undefined) {
				return value;
			}
			if (
				value instanceof RegExp ||
				typeof value === "bigInt" ||
				typeof value === "number" ||
				value instanceof Boolean ||
				value instanceof Number ||
				typeof value === "symbol"
			) {
				return value.__toString();
			}
			if (typeof value === "function") {
				return Function.prototype.__toString(value);
			}
			if (value instanceof Node) {
				return "Node";
			}
			if (value instanceof HTMLElement) {
				return "HTMLElement";
			}
			if (value?.constructor?.name === "DOMTokenList") {
				return "DOMTokenList";
			}
			if (value instanceof Selection) {
				return "Selection";
			}
			if (value?.self === value && value?.window === value) {
				return "window";
			}
			if (typeof value !== "object" || value === null) {
				return value;
			}
			if (ancestors.__has(value)) {
				return "[Circular]";
			}
			ancestors.__add(value);
			return value;
		};
	};
	window.counter = 0;
	let seen_data = new Set();

	// Sends data to the server through dedicated crawler-exposed method.
	window.__dispatchHookData = async function (api, data) {
		if (window.counter > 20000) {
			return;
		}
		let parsed_data;
		try {
			parsed_data = window.__stringify.__apply(this, [
				{
					type: api,
					data,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer(),
			]);
			window.__fetch(`${location.origin}${window.location.pathname}hook`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: parsed_data,
			});
		} catch (e) {
			if (window.__exposedErrorLogger) {
				window.__exposedErrorLogger({
					type: "html",
					source: "__dispatchHookData",
					error: e,
				});
			} else {
				console.__error({
					type: "html",
					source: "__dispatchHookData",
					error: e,
				});
			}
		}
		window.counter++;
	};

	window.__dispatchPollData = async function (data, stage) {
		let parsed_data;
		try {
			parsed_data = window.__stringify.__apply(this, [
				{
					data,
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer(),
			]);
			if (stage === "beforeunload") {
				navigator.sendBeacon(
					`${location.origin}${window.location.pathname}poll`,
					parsed_data
				);
			} else {
				window.__fetch(`${location.origin}${window.location.pathname}poll`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: parsed_data,
				});
			}
		} catch (e) {
			if (window.__exposedErrorLogger) {
				window.__exposedErrorLogger({
					type: "html",
					source: "__dispatchPollData",
					error: e,
				});
			} else {
				console.__error({
					type: "html",
					source: "__dispatchPollData",
					error: e,
				});
			}
		}
	};
})();

// Storage Proxy
(() => {
	function _storageProxy(object) {
		let old = window[object];
		let _storageObject = window[object];
		let _setItem = _storageObject.setItem;
		let _removeItem = _storageObject.removeItem;
		let _key = _storageObject.key;
		let _clear = _storageObject.clear;

		let hooked_assignment = function (prop, value) {
			let storageData = {
				type: `${object}.setItem`,
				arguments: {
					prop,
					value
				}
			}
			window.__dispatchHookData(`${object}.setItem`, storageData);
			return _setItem.__apply(_storageObject, arguments);
		}

		let hooked_get = function (prop) {
			let storageData = {
				type: `${object}.getItem`,
				arguments: prop,
				dis: _storageObject[prop]
			}
			window.__dispatchHookData(`${object}.getItem`, storageData);
			return _storageObject[prop];
		}

		let hooked_remove = function (prop) {
			let storageData = {
				type: `${object}.removeItem`,
				arguments: prop,
				dis: _storageObject[prop]
			}
			window.__dispatchHookData(`${object}.removeItem`, storageData);
			return _removeItem.__apply(_storageObject, arguments);
		}

		let hooked_key = function (prop) {
			let key = _key.__apply(_storageObject, arguments);
			let storageData = {
				type: `${object}.key`,
				dis: {
					prop,
					key
				}
			};
			window.__dispatchHookData(`${object}.key`, storageData);
			return key;
		};

		let hooked_clear = function () {
			let storageData = {
				type: `${object}.clear`,
				dis: "",
			};
			window.__dispatchHookData(`${object}.clear`, storageData);
			return _clear.__apply(_storageObject, arguments);
		};

		let hooked_length = function () {
			let len = _storageObject.length;
			let storageData = {
				type: `${object}.length`,
				dis: len,
			};
			window.__dispatchHookData(`${object}.length`, storageData);
			return len;
		};

		const handler = {
			get: function (object, property) {
				if (property === "setItem") return hooked_assignment;
				if (property === "getItem") return hooked_get;
				if (property === "removeItem") return hooked_remove;
				if (property === "key") return hooked_key;
				if (property === "clear") return hooked_clear;
				if (property === "length") return hooked_length();
				let accessed = object[property];
				if (accessed !== undefined && typeof accessed === "function") {
					accessed = accessed.__bind(old);
				}

				return accessed;
			},
			set: function (object, property, value) {
				if (property === "setItem" || property === "getItem" || property === "removeItem" || property ===
					"clear" || property === "key" || property === "length") return;
				let storageData = {
					type: `${object}.setItem`,
					arguments: {
						property,
						value
					}
				}
				window.__dispatchHookData(`${object}.setItem`, storageData);
				return object[property] = value;
			}
		}
		try {
			let proxy = new Proxy(_storageObject, handler);
			Object.__defineProperty(window, object, {
				get: () => {
					return proxy;
				}
			});
		} catch (e) { }
	};

	_storageProxy("localStorage");
	_storageProxy("sessionStorage");
})();

// MD5 Script
(function (factory) {
	if (typeof exports === "object") {
		module.exports = factory();
	} else if (typeof define === "function" && define.amd) {
		define(factory);
	} else {
		var glob;
		try {
			glob = window;
		} catch (e) {
			glob = self;
		}
		glob.SparkMD5 = factory();
	}
})(function (undefined) {
	"use strict";
	var add32 = function (a, b) {
		return (a + b) & 4294967295;
	},
		hex_chr = [
			"0",
			"1",
			"2",
			"3",
			"4",
			"5",
			"6",
			"7",
			"8",
			"9",
			"a",
			"b",
			"c",
			"d",
			"e",
			"f",
		];
	function cmn(q, a, b, x, s, t) {
		a = add32(add32(a, q), add32(x, t));
		return add32((a << s) | (a >>> (32 - s)), b);
	}
	function md5cycle(x, k) {
		var a = x[0],
			b = x[1],
			c = x[2],
			d = x[3];
		a += (((b & c) | (~b & d)) + k[0] - 680876936) | 0;
		a = (((a << 7) | (a >>> 25)) + b) | 0;
		d += (((a & b) | (~a & c)) + k[1] - 389564586) | 0;
		d = (((d << 12) | (d >>> 20)) + a) | 0;
		c += (((d & a) | (~d & b)) + k[2] + 606105819) | 0;
		c = (((c << 17) | (c >>> 15)) + d) | 0;
		b += (((c & d) | (~c & a)) + k[3] - 1044525330) | 0;
		b = (((b << 22) | (b >>> 10)) + c) | 0;
		a += (((b & c) | (~b & d)) + k[4] - 176418897) | 0;
		a = (((a << 7) | (a >>> 25)) + b) | 0;
		d += (((a & b) | (~a & c)) + k[5] + 1200080426) | 0;
		d = (((d << 12) | (d >>> 20)) + a) | 0;
		c += (((d & a) | (~d & b)) + k[6] - 1473231341) | 0;
		c = (((c << 17) | (c >>> 15)) + d) | 0;
		b += (((c & d) | (~c & a)) + k[7] - 45705983) | 0;
		b = (((b << 22) | (b >>> 10)) + c) | 0;
		a += (((b & c) | (~b & d)) + k[8] + 1770035416) | 0;
		a = (((a << 7) | (a >>> 25)) + b) | 0;
		d += (((a & b) | (~a & c)) + k[9] - 1958414417) | 0;
		d = (((d << 12) | (d >>> 20)) + a) | 0;
		c += (((d & a) | (~d & b)) + k[10] - 42063) | 0;
		c = (((c << 17) | (c >>> 15)) + d) | 0;
		b += (((c & d) | (~c & a)) + k[11] - 1990404162) | 0;
		b = (((b << 22) | (b >>> 10)) + c) | 0;
		a += (((b & c) | (~b & d)) + k[12] + 1804603682) | 0;
		a = (((a << 7) | (a >>> 25)) + b) | 0;
		d += (((a & b) | (~a & c)) + k[13] - 40341101) | 0;
		d = (((d << 12) | (d >>> 20)) + a) | 0;
		c += (((d & a) | (~d & b)) + k[14] - 1502002290) | 0;
		c = (((c << 17) | (c >>> 15)) + d) | 0;
		b += (((c & d) | (~c & a)) + k[15] + 1236535329) | 0;
		b = (((b << 22) | (b >>> 10)) + c) | 0;
		a += (((b & d) | (c & ~d)) + k[1] - 165796510) | 0;
		a = (((a << 5) | (a >>> 27)) + b) | 0;
		d += (((a & c) | (b & ~c)) + k[6] - 1069501632) | 0;
		d = (((d << 9) | (d >>> 23)) + a) | 0;
		c += (((d & b) | (a & ~b)) + k[11] + 643717713) | 0;
		c = (((c << 14) | (c >>> 18)) + d) | 0;
		b += (((c & a) | (d & ~a)) + k[0] - 373897302) | 0;
		b = (((b << 20) | (b >>> 12)) + c) | 0;
		a += (((b & d) | (c & ~d)) + k[5] - 701558691) | 0;
		a = (((a << 5) | (a >>> 27)) + b) | 0;
		d += (((a & c) | (b & ~c)) + k[10] + 38016083) | 0;
		d = (((d << 9) | (d >>> 23)) + a) | 0;
		c += (((d & b) | (a & ~b)) + k[15] - 660478335) | 0;
		c = (((c << 14) | (c >>> 18)) + d) | 0;
		b += (((c & a) | (d & ~a)) + k[4] - 405537848) | 0;
		b = (((b << 20) | (b >>> 12)) + c) | 0;
		a += (((b & d) | (c & ~d)) + k[9] + 568446438) | 0;
		a = (((a << 5) | (a >>> 27)) + b) | 0;
		d += (((a & c) | (b & ~c)) + k[14] - 1019803690) | 0;
		d = (((d << 9) | (d >>> 23)) + a) | 0;
		c += (((d & b) | (a & ~b)) + k[3] - 187363961) | 0;
		c = (((c << 14) | (c >>> 18)) + d) | 0;
		b += (((c & a) | (d & ~a)) + k[8] + 1163531501) | 0;
		b = (((b << 20) | (b >>> 12)) + c) | 0;
		a += (((b & d) | (c & ~d)) + k[13] - 1444681467) | 0;
		a = (((a << 5) | (a >>> 27)) + b) | 0;
		d += (((a & c) | (b & ~c)) + k[2] - 51403784) | 0;
		d = (((d << 9) | (d >>> 23)) + a) | 0;
		c += (((d & b) | (a & ~b)) + k[7] + 1735328473) | 0;
		c = (((c << 14) | (c >>> 18)) + d) | 0;
		b += (((c & a) | (d & ~a)) + k[12] - 1926607734) | 0;
		b = (((b << 20) | (b >>> 12)) + c) | 0;
		a += ((b ^ c ^ d) + k[5] - 378558) | 0;
		a = (((a << 4) | (a >>> 28)) + b) | 0;
		d += ((a ^ b ^ c) + k[8] - 2022574463) | 0;
		d = (((d << 11) | (d >>> 21)) + a) | 0;
		c += ((d ^ a ^ b) + k[11] + 1839030562) | 0;
		c = (((c << 16) | (c >>> 16)) + d) | 0;
		b += ((c ^ d ^ a) + k[14] - 35309556) | 0;
		b = (((b << 23) | (b >>> 9)) + c) | 0;
		a += ((b ^ c ^ d) + k[1] - 1530992060) | 0;
		a = (((a << 4) | (a >>> 28)) + b) | 0;
		d += ((a ^ b ^ c) + k[4] + 1272893353) | 0;
		d = (((d << 11) | (d >>> 21)) + a) | 0;
		c += ((d ^ a ^ b) + k[7] - 155497632) | 0;
		c = (((c << 16) | (c >>> 16)) + d) | 0;
		b += ((c ^ d ^ a) + k[10] - 1094730640) | 0;
		b = (((b << 23) | (b >>> 9)) + c) | 0;
		a += ((b ^ c ^ d) + k[13] + 681279174) | 0;
		a = (((a << 4) | (a >>> 28)) + b) | 0;
		d += ((a ^ b ^ c) + k[0] - 358537222) | 0;
		d = (((d << 11) | (d >>> 21)) + a) | 0;
		c += ((d ^ a ^ b) + k[3] - 722521979) | 0;
		c = (((c << 16) | (c >>> 16)) + d) | 0;
		b += ((c ^ d ^ a) + k[6] + 76029189) | 0;
		b = (((b << 23) | (b >>> 9)) + c) | 0;
		a += ((b ^ c ^ d) + k[9] - 640364487) | 0;
		a = (((a << 4) | (a >>> 28)) + b) | 0;
		d += ((a ^ b ^ c) + k[12] - 421815835) | 0;
		d = (((d << 11) | (d >>> 21)) + a) | 0;
		c += ((d ^ a ^ b) + k[15] + 530742520) | 0;
		c = (((c << 16) | (c >>> 16)) + d) | 0;
		b += ((c ^ d ^ a) + k[2] - 995338651) | 0;
		b = (((b << 23) | (b >>> 9)) + c) | 0;
		a += ((c ^ (b | ~d)) + k[0] - 198630844) | 0;
		a = (((a << 6) | (a >>> 26)) + b) | 0;
		d += ((b ^ (a | ~c)) + k[7] + 1126891415) | 0;
		d = (((d << 10) | (d >>> 22)) + a) | 0;
		c += ((a ^ (d | ~b)) + k[14] - 1416354905) | 0;
		c = (((c << 15) | (c >>> 17)) + d) | 0;
		b += ((d ^ (c | ~a)) + k[5] - 57434055) | 0;
		b = (((b << 21) | (b >>> 11)) + c) | 0;
		a += ((c ^ (b | ~d)) + k[12] + 1700485571) | 0;
		a = (((a << 6) | (a >>> 26)) + b) | 0;
		d += ((b ^ (a | ~c)) + k[3] - 1894986606) | 0;
		d = (((d << 10) | (d >>> 22)) + a) | 0;
		c += ((a ^ (d | ~b)) + k[10] - 1051523) | 0;
		c = (((c << 15) | (c >>> 17)) + d) | 0;
		b += ((d ^ (c | ~a)) + k[1] - 2054922799) | 0;
		b = (((b << 21) | (b >>> 11)) + c) | 0;
		a += ((c ^ (b | ~d)) + k[8] + 1873313359) | 0;
		a = (((a << 6) | (a >>> 26)) + b) | 0;
		d += ((b ^ (a | ~c)) + k[15] - 30611744) | 0;
		d = (((d << 10) | (d >>> 22)) + a) | 0;
		c += ((a ^ (d | ~b)) + k[6] - 1560198380) | 0;
		c = (((c << 15) | (c >>> 17)) + d) | 0;
		b += ((d ^ (c | ~a)) + k[13] + 1309151649) | 0;
		b = (((b << 21) | (b >>> 11)) + c) | 0;
		a += ((c ^ (b | ~d)) + k[4] - 145523070) | 0;
		a = (((a << 6) | (a >>> 26)) + b) | 0;
		d += ((b ^ (a | ~c)) + k[11] - 1120210379) | 0;
		d = (((d << 10) | (d >>> 22)) + a) | 0;
		c += ((a ^ (d | ~b)) + k[2] + 718787259) | 0;
		c = (((c << 15) | (c >>> 17)) + d) | 0;
		b += ((d ^ (c | ~a)) + k[9] - 343485551) | 0;
		b = (((b << 21) | (b >>> 11)) + c) | 0;
		x[0] = (a + x[0]) | 0;
		x[1] = (b + x[1]) | 0;
		x[2] = (c + x[2]) | 0;
		x[3] = (d + x[3]) | 0;
	}
	function md5blk(s) {
		var md5blks = [],
			i;
		for (i = 0; i < 64; i += 4) {
			md5blks[i >> 2] =
				s.__charCodeAt(i) +
				(s.__charCodeAt(i + 1) << 8) +
				(s.__charCodeAt(i + 2) << 16) +
				(s.__charCodeAt(i + 3) << 24);
		}
		return md5blks;
	}
	function md5blk_array(a) {
		var md5blks = [],
			i;
		for (i = 0; i < 64; i += 4) {
			md5blks[i >> 2] =
				a[i] + (a[i + 1] << 8) + (a[i + 2] << 16) + (a[i + 3] << 24);
		}
		return md5blks;
	}
	function md51(s) {
		var n = s.length,
			state = [1732584193, -271733879, -1732584194, 271733878],
			i,
			length,
			tail,
			tmp,
			lo,
			hi;
		for (i = 64; i <= n; i += 64) {
			md5cycle(state, md5blk(s.__substring(i - 64, i)));
		}
		s = s.__substring(i - 64);
		length = s.length;
		tail = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
		for (i = 0; i < length; i += 1) {
			tail[i >> 2] |= s.__charCodeAt(i) << (i % 4 << 3);
		}
		tail[i >> 2] |= 128 << (i % 4 << 3);
		if (i > 55) {
			md5cycle(state, tail);
			for (i = 0; i < 16; i += 1) {
				tail[i] = 0;
			}
		}
		tmp = n * 8;
		tmp = splitLastPart(tmp.__toString(16));
		lo = __parseInt(tmp[2], 16);
		hi = __parseInt(tmp[1], 16) || 0;
		tail[14] = lo;
		tail[15] = hi;
		md5cycle(state, tail);
		return state;
	}
	function splitLastPart(str) {
		const length = str.length;
		const part2 = str.__slice(-8);  // Get the last 0 to 8 characters
		const part1 = str.__slice(0, length - part2.length); // Everything before that
		return [part1, part2];
	}
	function md51_array(a) {
		var n = a.length,
			state = [1732584193, -271733879, -1732584194, 271733878],
			i,
			length,
			tail,
			tmp,
			lo,
			hi;
		for (i = 64; i <= n; i += 64) {
			md5cycle(state, md5blk_array(a.__subarray(i - 64, i)));
		}
		a = i - 64 < n ? a.__subarray(i - 64) : new Uint8Array(0);
		length = a.length;
		tail = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
		for (i = 0; i < length; i += 1) {
			tail[i >> 2] |= a[i] << (i % 4 << 3);
		}
		tail[i >> 2] |= 128 << (i % 4 << 3);
		if (i > 55) {
			md5cycle(state, tail);
			for (i = 0; i < 16; i += 1) {
				tail[i] = 0;
			}
		}
		tmp = n * 8;
		tmp = splitLastPart(tmp.__toString(16));
		lo = __parseInt(tmp[2], 16);
		hi = __parseInt(tmp[1], 16) || 0;
		tail[14] = lo;
		tail[15] = hi;
		md5cycle(state, tail);
		return state;
	}
	function rhex(n) {
		var s = "",
			j;
		for (j = 0; j < 4; j += 1) {
			s +=
				hex_chr[(n >> (j * 8 + 4)) & 15] + hex_chr[(n >> (j * 8)) & 15];
		}
		return s;
	}
	function hex(x) {
		var i;
		for (i = 0; i < x.length; i += 1) {
			x[i] = rhex(x[i]);
		}
		return x.__join("");
	}
	if (hex(md51("hello")) !== "5d41402abc4b2a76b9719d911017c592") {
		add32 = function (x, y) {
			var lsw = (x & 65535) + (y & 65535),
				msw = (x >> 16) + (y >> 16) + (lsw >> 16);
			return (msw << 16) | (lsw & 65535);
		};
	}
	if (
		typeof ArrayBuffer !== "undefined" &&
		!ArrayBuffer.prototype.slice
	) {
		(function () {
			function clamp(val, length) {
				val = val | 0 || 0;
				if (val < 0) {
					return Math.__max(val + length, 0);
				}
				return Math.__min(val, length);
			}
			ArrayBuffer.prototype.slice = function (from, to) {
				var length = this.byteLength,
					begin = clamp(from, length),
					end = length,
					num,
					target,
					targetArray,
					sourceArray;
				if (to !== undefined) {
					end = clamp(to, length);
				}
				if (begin > end) {
					return new ArrayBuffer(0);
				}
				num = end - begin;
				target = new ArrayBuffer(num);
				targetArray = new Uint8Array(target);
				sourceArray = new Uint8Array(this, begin, num);
				targetArray.set(sourceArray);
				return target;
			};
		})();
	}
	function hasHighUnicodeChar(str) {
		for (let i = 0; i < str.length; i++) {
			let code = str.__charCodeAt(i);
			if (code >= 0x0080 && code <= 0xffff) {
				return true;
			}
		}
		return false;
	}
	function toUtf8(str) {
		if (hasHighUnicodeChar(str)) {
			str = __unescape(__encodeURIComponent(str));
		}
		return str;
	}
	function utf8Str2ArrayBuffer(str, returnUInt8Array) {
		var length = str.length,
			buff = new ArrayBuffer(length),
			arr = new Uint8Array(buff),
			i;
		for (i = 0; i < length; i += 1) {
			arr[i] = str.__charCodeAt(i);
		}
		return returnUInt8Array ? arr : buff;
	}
	function arrayBuffer2Utf8Str(buff) {
		return String.__fromCharCode.__apply(null, new Uint8Array(buff));
	}
	function concatenateArrayBuffers(first, second, returnUInt8Array) {
		var result = new Uint8Array(first.byteLength + second.byteLength);
		result.set(new Uint8Array(first));
		result.set(new Uint8Array(second), first.byteLength);
		return returnUInt8Array ? result : result.buffer;
	}
	function hexToBinaryString(hex) {
		var bytes = [],
			length = hex.length,
			x;
		for (x = 0; x < length - 1; x += 2) {
			bytes.__push(__parseInt(hex.__substr(x, 2), 16));
		}
		return String.__fromCharCode.__apply(String, bytes);
	}
	function SparkMD5() {
		this.reset();
	}
	SparkMD5.prototype.append = function (str) {
		this.appendBinary(toUtf8(str));
		return this;
	};
	SparkMD5.prototype.appendBinary = function (contents) {
		this._buff += contents;
		this._length += contents.length;
		var length = this._buff.length,
			i;
		for (i = 64; i <= length; i += 64) {
			md5cycle(this._hash, md5blk(this._buff.__substring(i - 64, i)));
		}
		this._buff = this._buff.__substring(i - 64);
		return this;
	};
	SparkMD5.prototype.end = function (raw) {
		var buff = this._buff,
			length = buff.length,
			i,
			tail = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
			ret;
		for (i = 0; i < length; i += 1) {
			tail[i >> 2] |= buff.__charCodeAt(i) << (i % 4 << 3);
		}
		this._finish(tail, length);
		ret = hex(this._hash);
		if (raw) {
			ret = hexToBinaryString(ret);
		}
		this.reset();
		return ret;
	};
	SparkMD5.prototype.reset = function () {
		this._buff = "";
		this._length = 0;
		this._hash = [1732584193, -271733879, -1732584194, 271733878];
		return this;
	};
	SparkMD5.prototype.getState = function () {
		return {
			buff: this._buff,
			length: this._length,
			hash: this._hash.slice(),
		};
	};
	SparkMD5.prototype.setState = function (state) {
		this._buff = state.buff;
		this._length = state.length;
		this._hash = state.hash;
		return this;
	};
	SparkMD5.prototype.destroy = function () {
		delete this._hash;
		delete this._buff;
		delete this._length;
	};
	SparkMD5.prototype._finish = function (tail, length) {
		var i = length,
			tmp,
			lo,
			hi;
		tail[i >> 2] |= 128 << (i % 4 << 3);
		if (i > 55) {
			md5cycle(this._hash, tail);
			for (i = 0; i < 16; i += 1) {
				tail[i] = 0;
			}
		}
		tmp = this._length * 8;
		tmp = splitLastPart(tmp.__toString(16));
		lo = __parseInt(tmp[2], 16);
		hi = __parseInt(tmp[1], 16) || 0;
		tail[14] = lo;
		tail[15] = hi;
		md5cycle(this._hash, tail);
	};
	SparkMD5.hash = function (str, raw) {
		return SparkMD5.hashBinary(toUtf8(str), raw);
	};
	SparkMD5.hashBinary = function (content, raw) {
		var hash = md51(content),
			ret = hex(hash);
		return raw ? hexToBinaryString(ret) : ret;
	};
	SparkMD5.ArrayBuffer = function () {
		this.reset();
	};
	SparkMD5.ArrayBuffer.prototype.append = function (arr) {
		var buff = concatenateArrayBuffers(this._buff.buffer, arr, true),
			length = buff.length,
			i;
		this._length += arr.byteLength;
		for (i = 64; i <= length; i += 64) {
			md5cycle(this._hash, md5blk_array(buff.__subarray(i - 64, i)));
		}
		this._buff =
			i - 64 < length
				? new Uint8Array(buff.buffer.slice(i - 64))
				: new Uint8Array(0);
		return this;
	};
	SparkMD5.ArrayBuffer.prototype.end = function (raw) {
		var buff = this._buff,
			length = buff.length,
			tail = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
			i,
			ret;
		for (i = 0; i < length; i += 1) {
			tail[i >> 2] |= buff[i] << (i % 4 << 3);
		}
		this._finish(tail, length);
		ret = hex(this._hash);
		if (raw) {
			ret = hexToBinaryString(ret);
		}
		this.reset();
		return ret;
	};
	SparkMD5.ArrayBuffer.prototype.reset = function () {
		this._buff = new Uint8Array(0);
		this._length = 0;
		this._hash = [1732584193, -271733879, -1732584194, 271733878];
		return this;
	};
	SparkMD5.ArrayBuffer.prototype.getState = function () {
		var state = SparkMD5.prototype.getState.call(this);
		state.buff = arrayBuffer2Utf8Str(state.buff);
		return state;
	};
	SparkMD5.ArrayBuffer.prototype.setState = function (state) {
		state.buff = utf8Str2ArrayBuffer(state.buff, true);
		return SparkMD5.prototype.setState.call(this, state);
	};
	SparkMD5.ArrayBuffer.prototype.destroy = SparkMD5.prototype.destroy;
	SparkMD5.ArrayBuffer.prototype._finish = SparkMD5.prototype._finish;
	SparkMD5.ArrayBuffer.hash = function (arr, raw) {
		var hash = md51_array(new Uint8Array(arr)),
			ret = hex(hash);
		return raw ? hexToBinaryString(ret) : ret;
	};
	return SparkMD5;
});

// Content Script related interactions from the FP project
(() => {
	async function getIndexedDBData() {
		let idbPromise = new Promise((resolve) => {
			let totalDBData = {};
			totalDBData.type = "idb";
			if (indexedDB.__databases === undefined) return;
			indexedDB.__databases().then((r) =>
				r.__forEach((element) => {
					totalDBData.dbName = element.name;
					totalDBData.dataValues = [];
					indexedDB.__open(element.name).onsuccess = function (
						sender,
						args
					) {
						let db = sender.target.result;
						let storeIndex = 0;
						let storesData = [];
						while (
							storeIndex < sender.target.result.objectStoreNames.length
						) {
							let trans = db.__transaction(
								sender.target.result.objectStoreNames[storeIndex],
								"readwrite"
							);
							let store = trans.__objectStore(
								sender.target.result.objectStoreNames[storeIndex]
							);
							let storeData = {};
							storeData.storeValues = {};
							store.__openCursor().onsuccess = function (event) {
								storeData["storeName"] = event.target.source.name;
								let cursor = event.target.result;
								if (cursor) {
									storeData.storeValues[cursor.primaryKey] = cursor.value;
									cursor.__continue();
								}
							};
							storeIndex = storeIndex + 1;
							storesData.__push(storeData);
						}

						let dbData = {};
						dbData.databaseName = element.name;
						dbData.databaseValues = [];
						dbData.databaseValues.__push(storesData);
						totalDBData.dataValues.__push(dbData);
					};
				})
			);
			resolve(totalDBData);
		});
		return idbPromise;
	}

	async function __pollStorage(stage = "poll") {
		try {
			let localStorageData = {};
			let sessionStorageData = {};

			if (indexedDB.__databases !== undefined && chrome !== undefined) {
				await getIndexedDBData()
					.then((result) => {
						return result;
					})
					.then((totalDBData) => {
						__setTimeout(async () => {
							if (
								totalDBData?.dataValues !== undefined &&
								totalDBData?.dbName !== undefined
							)
								__dispatchPollData({
									type: "idb",
									stage: stage,
									url: window.top.location.href,
									data: totalDBData,
								}, stage);
						}, 2000);
					});
			}

			let variables = {};
			for (let prop of Object.__getOwnPropertyNames(window)) {
				if (seenVars.__has(prop)) continue;
				try {
					__value = undefined;
					if (typeof window[prop] === "object") {
						__value = window.__stringify(window[prop]);
					}
					if (__value?.__toString()?.length > 100) {
						variables[prop] = window.__stringify(window[prop])?.__slice(0, 100);
					} else {
						variables[prop] = window[prop];
					}
				} catch (e) {
					variables[prop] = window[prop];
				}
			}
			for (let prop of Object.__getOwnPropertyNames(document)) {
				if (prop === "location" || seenVars.__has(prop)) continue;
				variables[prop] = "";
			}
			if (Object.__keys(variables).length > 0) {
				for (let key of Object.__keys(variables)) {
					try {
						window.__stringify(
							variables[key],
							window.__getCircularReplacer()
						);
					} catch (e) {
						delete variables[key];
					}
				}

				__dispatchPollData({
					data: {
						variables,
					},
					type: "variable",
					script: "",
					url: window.location.href,
					contextURL: document.location.href,
					stage: "poll",
				}, stage);
			}
			for (let key of Object.__getOwnPropertyNames(window.__ls)) {
				localStorageData[key] = window.__ls[key];
			}
			for (let key of Object.__getOwnPropertyNames(window.__ss)) {
				sessionStorageData[key] = window.__ss[key];
			}
			if (Object.__keys(localStorageData).length) {
				__dispatchPollData({
					type: "local",
					stage: stage,
					url: window.top.location.href,
					data: localStorageData,
				}, stage);
			}

			if (Object.__keys(sessionStorageData).length) {
				__dispatchPollData({
					type: "session",
					stage: stage,
					url: window.top.location.href,
					data: sessionStorageData,
				}, stage);
			}

			if (window.__cookieGetter()) {
				__dispatchPollData({
					type: "cookies",
					stage: stage,
					url: window.top.location.href,
					data: window.__cookieGetter(),
				}, stage);
			}
		} catch (e) {
			if (window.__exposedErrorLogger) {
				window.__exposedErrorLogger({
					type: "html",
					source: "__pollStorage",
					error: e,
				});
			} else {
				console.__error({
					type: "html",
					source: "__pollStorage",
					error: e,
				});
			}
		}
	}
})();

// JS Property Hooks
(() => {
	function __hookProperty(
		object,
		property,
		tag,
		getter = false,
		setter = false
	) {
		try {
			let __propGetter, __propSetter;
			try {
				__propGetter =
					object["___lookupGetter___"](property).__bind(object);
			} catch (e) {
				__propGetter = function () { };
			}

			try {
				__propSetter =
					object["___lookupSetter___"](property).__bind(object);
			} catch (e) {
				__propSetter = function () { };
			}

			let __hookedGetter = function () {
				let data, caller, callerString, callerName, callerData, stacktrace;
				try {
					data = __propGetter(...arguments);
					try {
						caller = arguments?.callee?.caller;
						callerString = caller?.__toString();
						callerName = caller?.name;
						if (callerString.__startsWith("async function (api, data)")) {
							callerString = undefined;
							caller = undefined;
						} else if (
							callerName.__startsWith("_hook") ||
							callerName.__startsWith("__hook")
						) {
							caller = caller?.arguments?.callee?.caller;
							callerString = caller?.__toString();
							callerName = caller?.name;
						}
					} catch (e) { }

					try {
						stacktrace = new Error().stack.__split("\n");
						stacktrace.__shift();
						stacktrace.__shift();
					} catch (e) { }

					try {
						callerData = {};
						let seenCallers = new WeakSet();
						while (true && caller != null && caller != "") {
							if (seenCallers.__has(caller)) break;
							seenCallers.__add(caller);
							parent_caller = caller?.arguments?.callee?.caller;
							parent_caller_name = parent_caller?.name;
							parent_caller_string = parent_caller?.__toString();
							if (
								Object.__keys(callerData).__includes(parent_caller_name)
							) {
								callerData[parent_caller_name].__push(parent_caller_string);
							} else {
								callerData[parent_caller_name] = [parent_caller_string];
							}
							caller = parent_caller;
						}
					} catch (e) { }
					let detail = {
						type: tag,
						dis: data,
						arguments,
						caller: callerString,
						callerName,
						callerData,
						stacktrace,
						url: window.location.href,
						contextURL: document.location.href,
					};
					if (window.__stringify(stacktrace)?.__indexOf("_hooked") > -1)
						return data;
					try {
						window.__dispatchHookData(tag, detail);
					} catch (e) { }
				} catch (e) {
					if (window.__exposedErrorLogger) {
						window.__exposedErrorLogger({
							type: "html",
							source: "__hookedGetter",
							error: e,
						});
					} else {
						console.__error({
							type: "html",
							source: "__hookedGetter",
							error: e,
						});
					}
				} finally {
					return data;
				}
			};

			let __hookedSetter = function () {
				let data, caller, callerString, callerName, callerData, stacktrace;
				try {
					data = __propSetter(...arguments);
					try {
						caller = arguments?.callee?.caller;
						callerString = caller?.__toString();
						callerName = caller?.name;
						if (callerString.__startsWith("async function (api, data)")) {
							callerString = undefined;
							caller = undefined;
						} else if (
							callerName.__startsWith("_hook") ||
							callerName.__startsWith("__hook")
						) {
							caller = caller?.arguments?.callee?.caller;
							callerString = caller?.__toString();
							callerName = caller?.name;
						}
					} catch (e) { }

					try {
						stacktrace = new Error().stack.__split("\n");
						stacktrace.__shift();
						stacktrace.__shift();
					} catch (e) { }

					try {
						callerData = {};
						let seenCallers = new WeakSet();
						while (true && caller != null && caller != "") {
							if (seenCallers.__has(caller)) break;
							seenCallers.__add(caller);
							parent_caller = caller?.arguments?.callee?.caller;
							parent_caller_name = parent_caller?.name;
							parent_caller_string = parent_caller?.__toString();
							if (
								Object.__keys(callerData).__includes(parent_caller_name)
							) {
								callerData[parent_caller_name].__push(parent_caller_string);
							} else {
								callerData[parent_caller_name] = [parent_caller_string];
							}
							caller = parent_caller;
						}
					} catch (e) { }
					let detail = {
						type: tag,
						dis: data,
						arguments,
						caller: callerString,
						callerName,
						callerData,
						stacktrace,
						url: window.location.href,
						contextURL: document.location.href,
					};
					if (window.__stringify(stacktrace)?.__indexOf("_hooked") > -1)
						return data;
					try {
						window.__dispatchHookData(tag, detail);
					} catch (e) { }
				} catch (e) {
					if (window.__exposedErrorLogger) {
						window.__exposedErrorLogger({
							type: "html",
							source: "__hookedSetter",
							error: e,
						});
					} else {
						console.__error({
							type: "html",
							source: "__hookedSetter",
							error: e,
						});
					}
				} finally {
					return data;
				}
			};

			let __defaultGetter = function () {
				return __propGetter(...arguments);
			};

			let __defaultSetter = function () {
				return __propSetter(...arguments);
			};

			Object.defineProperty(object, property, {
				get: getter ? __hookedGetter : __defaultGetter,
				set: setter ? __hookedSetter : __defaultSetter,
			});
		} catch (e) {
			if (window.__exposedErrorLogger) {
				window.__exposedErrorLogger({
					type: "html",
					source: "__hookProperty",
					error: e,
				});
			} else {
				console.__error({
					type: "html",
					source: "__hookProperty",
					error: e,
				});
			}
		}
	}

	__hookProperty(document, "alinkColor", "document.alinkColor", true, true);
	__hookProperty(document, "bgColor", "document.bgColor", true, true);
	__hookProperty(
		document,
		"characterSet",
		"document.characterSet",
		true,
		false
	);
	__hookProperty(
		document,
		"childElementCount",
		"document.childElementCount",
		true,
		false
	);
	__hookProperty(
		document,
		"compatMode",
		"document.compatMode",
		true,
		false
	);
	__hookProperty(
		document,
		"contentType",
		"document.contentType",
		true,
		false
	);
	__hookProperty(document, "cookie", "document.cookie", true, true);
	__hookProperty(
		document,
		"defaultView",
		"document.defaultView",
		true,
		false
	);
	__hookProperty(document, "designMode", "document.designMode", true, true);
	__hookProperty(document, "dir", "document.dir", true, true);
	__hookProperty(document, "domain", "document.domain", true, true);
	__hookProperty(
		document,
		"fragmentDirective",
		"document.fragmentDirective",
		true,
		false
	);
	__hookProperty(document, "fgColor", "document.fgColor", true, true);
	__hookProperty(
		document,
		"fullscreen",
		"document.fullscreen",
		true,
		false
	);
	__hookProperty(
		document,
		"fullscreenEnabled",
		"document.fullscreenEnabled",
		true,
		false
	);
	__hookProperty(document, "hidden", "document.hidden", true, false);
	__hookProperty(
		document,
		"lastModified",
		"document.lastModified",
		true,
		true
	);
	__hookProperty(
		document,
		"lastStyleSheetSet",
		"document.lastStyleSheetSet",
		true,
		true
	);
	__hookProperty(document, "linkColor", "document.linkColor", true, true);
	__hookProperty(
		document,
		"preferredStyleSheetSet",
		"document.preferredStyleSheetSet",
		true,
		true
	);
	__hookProperty(document, "referrer", "document.referrer", true, true);
	__hookProperty(document, "title", "document.title", true, true);
	__hookProperty(
		document,
		"visibilityState",
		"document.visibilityState",
		true,
		false
	);
	__hookProperty(document, "URL", "document.URL", true, false);
	__hookProperty(window, "closed", "window.closed", true, false);
	__hookProperty(
		window,
		"credentialless",
		"window.credentialless",
		true,
		false
	);
	__hookProperty(
		window,
		"defaultStatus",
		"window.defaultStatus",
		true,
		true
	);
	__hookProperty(window, "fullScreen", "window.fullScreen", true, false);
	__hookProperty(window, "innerHeight", "window.innerHeight", true, false);
	__hookProperty(window, "innerWidth", "window.innerWidth", true, false);
	__hookProperty(window, "length", "window.length", true, true);
	__hookProperty(
		window.locationbar,
		"visible",
		"window.locationbar.visible",
		true,
		false
	);
	__hookProperty(
		window.menubar,
		"visible",
		"window.menubar.visible",
		true,
		false
	);
	__hookProperty(window, "name", "window.name", true, true);
	__hookProperty(window, "orientation", "window.orientation", true, false);
	__hookProperty(window, "outerHeight", "window.outerHeight", true, false);
	__hookProperty(window, "outerWidth", "window.outerWidth", true, false);
	__hookProperty(window, "pageXOffset", "window.pageXOffset", true, false);
	__hookProperty(window, "pageYOffset", "window.pageYOffset", true, false);
	__hookProperty(
		window.personalbar,
		"visible",
		"window.personalbar.visible",
		true,
		false
	);
	__hookProperty(window, "screenLeft", "window.screenLeft", true, false);
	__hookProperty(window, "screenTop", "window.screenTop", true, false);
	__hookProperty(window, "screenX", "window.screenX", true, false);
	__hookProperty(window, "screenY", "window.screenY", true, false);
	__hookProperty(window, "scrollMaxX", "window.scrollMaxX", true, false);
	__hookProperty(window, "scrollMaxY", "window.scrollMaxY", true, false);
	__hookProperty(window, "scrollX", "window.scrollX", true, false);
	__hookProperty(window, "scrollY", "window.scrollY", true, false);
	__hookProperty(window, "status", "window.status", true, true);
	__hookProperty(
		window.toolbar,
		"visible",
		"window.toolbar.visible",
		true,
		false
	);
	__hookProperty(
		window,
		"visualViewport",
		"window.visualViewport",
		true,
		false
	);

	if (navigator.userActivation) {
		__hookProperty(
			navigator.userActivation,
			"isActive",
			"navigator.userActivation.isActive",
			true,
			false
		);
		__hookProperty(
			navigator.userActivation,
			"hasBeenActive",
			"navigator.userActivation.hasBeenActive",
			true,
			false
		);
	}

	if (window.TrustedTypePolicyFactory) {
		__hookProperty(
			TrustedTypePolicyFactory.prototype,
			"emptyHTML",
			"TrustedTypePolicyFactory.emptyHTML",
			true,
			false
		);
		__hookProperty(
			TrustedTypePolicyFactory.prototype,
			"emptyScript",
			"TrustedTypePolicyFactory.emptyScript",
			true,
			false
		);
		__hookProperty(
			TrustedTypePolicyFactory.prototype,
			"defaultPolicy",
			"TrustedTypePolicyFactory.defaultPolicy",
			true,
			false
		);
	}
})();

// JS API Hooks
(() => {
	function __hook(object, property, tag) {
		try {
			let old_fun = object[property];

			function _hooked() {
				if (window.api_cnt.__get(tag) >= 5000) {
					if (old_fun === undefined) return undefined;
					else return old_fun.__apply(this, arguments);
				}

				let caller, callerString, callerName, callerData, stacktrace;
				try {
					caller = arguments?.callee?.caller;
					callerString = caller?.__toString();
					callerName = caller?.name;
					if (callerString.__startsWith("async function (api, data)")) {
						callerString = undefined;
						caller = undefined;
					} else if (callerName.__startsWith("_hooked")) {
						caller = caller?.arguments?.callee?.caller;
						callerString = caller?.__toString();
						callerName = caller?.name;
					}
				} catch (e) { }
				try {
					stacktrace = new Error().stack;
					stacktrace = stacktrace.__split("\n");
					stacktrace.__shift();
					stacktrace.__shift();
					// if (stacktrace.__split("_hooked").length > 2) {
					//     stacktrace = "skip";
					// } else {
					//     stacktrace = stacktrace.__split("\n");
					//     stacktrace.__shift();
					//     stacktrace.__shift();
					// }
				} catch (e) { }

				try {
					callerData = {};
					let seenCallers = new WeakSet();
					while (caller != null && caller.__toString() != "") {
						if (seenCallers.__has(caller)) break;
						seenCallers.__add(caller);
						parent_caller = caller?.arguments?.callee?.caller;
						parent_caller_name = parent_caller?.name;
						parent_caller_string = parent_caller?.__toString();
						if (
							Object.__keys(callerData).__includes(parent_caller_name)
						) {
							callerData[parent_caller_name].__push(parent_caller_string);
						} else {
							callerData[parent_caller_name] = [parent_caller_string];
						}
						caller = parent_caller;
					}
				} catch (e) { }
				window.api_cnt.__set(tag, (window.api_cnt.__get(tag) || 0) + 1);
				if (stacktrace !== "skip") {
					try {
						let hash;
						try {
							hash = SparkMD5.hash(
								window.__stringify(stacktrace)
							).toString();
						} catch (e) { }

						if (!seen_data.__has(hash) && stacktrace !== "skip") {
							seen_data.__add(hash);
							try {
								window.__dispatchHookData(tag, {
									dis: tag.__startsWith("Date.") ? undefined : this,
									caller: callerString,
									callerName,
									callerData,
									stacktrace,
									arguments: Array.__from(arguments),
									url: window.location.href,
									contextURL: document.location.href,
								});
							} catch (e) { }
						}
					} catch (e) {
						console.__error("Something wrong!", e.message);
					}
				}
				if (old_fun === undefined) return undefined;
				else return old_fun.__apply(this, arguments);
			}
			object[property] = _hooked;
		} catch (e) {
			if (window.__exposedErrorLogger) {
				window.__exposedErrorLogger({
					type: "html",
					source: "__hook",
					error: e,
				});
			} else {
				console.__error({ type: "html", source: "__hook", error: e });
			}
		}
	}

	__hook(Array.prototype, "forEach", "Array.forEach");
	__hook(Array.prototype, "at", "Array.at");
	__hook(Array.prototype, "includes", "Array.includes");
	__hook(Array.prototype, "concat", "Array.concat");
	__hook(Array.prototype, "every", "Array.every");
	__hook(Array.prototype, "filter", "Array.filter");
	__hook(Array.prototype, "join", "Array.join");
	__hook(Array.prototype, "lastIndexOf", "Array.lastIndexOf");
	__hook(Array.prototype, "map", "Array.map");
	__hook(Array.prototype, "pop", "Array.pop");
	__hook(Array.prototype, "push", "Array.push");
	__hook(Array.prototype, "reduce", "Array.reduce");
	__hook(Array.prototype, "entries", "Array.entries");
	__hook(Array.prototype, "fill", "Array.fill");
	__hook(Array.prototype, "find", "Array.find");
	__hook(Array.prototype, "findLastIndex", "Array.findLastIndex");
	__hook(Array.prototype, "findIndex", "Array.findIndex");
	__hook(Array.prototype, "findLast", "Array.findLast");
	__hook(Array.prototype, "flat", "Array.flat");
	__hook(Array.prototype, "keys", "Array.keys");
	__hook(Array.prototype, "toReversed", "Array.toReversed");
	__hook(Array.prototype, "toSorted", "Array.toSorted");
	__hook(Array.prototype, "toSpliced", "Array.toSpliced");
	__hook(Array.prototype, "values", "Array.values");
	__hook(Array.prototype, "toLocaleString", "Array.toLocaleString");
	__hook(Array.prototype, "some", "Array.some");
	__hook(Array.prototype, "copyWithin", "Array.copyWithin");
	__hook(Array.prototype, "reduceRight", "Array.reduceRight");
	__hook(Array.prototype, "reverse", "Array.reverse");
	__hook(Array.prototype, "shift", "Array.shift");
	__hook(Array.prototype, "slice", "Array.slice");
	__hook(Array.prototype, "sort", "Array.sort");
	__hook(Array.prototype, "splice", "Array.splice");
	__hook(Array.prototype, "toString", "Array.toString");
	__hook(Array.prototype, "unshift", "Array.unshift");
	__hook(Array, "from", "Array.from");
	__hook(Array, "isArray", "Array.isArray");
	__hook(Array, "of", "Array.of");

	__hook(BigInt.prototype, "toLocaleString", "BigInt.toLocaleString");
	__hook(BigInt.prototype, "toString", "BigInt.toString");
	__hook(BigInt.prototype, "valueOf", "BigInt.valueOf");
	__hook(BigInt, "asIntN", "BigInt.asIntN");
	__hook(BigInt, "asUintN", "BigInt.asUintN");

	__hook(Boolean.prototype, "toString", "Boolean.toString");
	__hook(Boolean.prototype, "valueOf", "Boolean.valueOf");

	__hook(console, "assert", "console.assert");
	__hook(console, "clear", "console.clear");
	__hook(console, "count", "console.count");
	__hook(console, "countReset", "console.countReset");
	__hook(console, "debug", "console.debug");
	__hook(console, "dir", "console.dir");
	__hook(console, "dirxml", "console.dirxml");
	__hook(console, "error", "console.error");
	__hook(console, "group", "console.group");
	__hook(console, "groupCollapsed", "console.groupCollapsed");
	__hook(console, "groupEnd", "console.groupEnd");
	__hook(console, "info", "console.info");
	__hook(console, "log", "console.log");
	__hook(console, "profile", "console.profile");
	__hook(console, "profileEnd", "console.profileEnd");
	__hook(console, "table", "console.table");
	__hook(console, "time", "console.time");
	__hook(console, "timeEnd", "console.timeEnd");
	__hook(console, "timeLog", "console.timeLog");
	__hook(console, "timeStamp", "console.timeStamp");
	__hook(console, "trace", "console.trace");
	__hook(console, "warn", "console.warn");

	__hook(Crypto.prototype, "getRandomValues", "Crypto.getRandomValues");
	__hook(Crypto.prototype, "randomUUID() ", "Crypto.randomUUID");

	__hook(Date.prototype, "getDate", "Date.getDate");
	__hook(Date.prototype, "getDay", "Date.getDay");
	__hook(Date.prototype, "getFullYear", "Date.getFullYear");
	__hook(Date.prototype, "getHours", "Date.getHours");
	__hook(Date.prototype, "getMilliseconds", "Date.getMilliseconds");
	__hook(Date.prototype, "getMinutes", "Date.getMinutes");
	__hook(Date.prototype, "getMonth", "Date.getMonth");
	__hook(Date.prototype, "getSeconds", "Date.getSeconds");
	__hook(Date.prototype, "getTime", "Date.getTime");
	__hook(Date.prototype, "getTimezoneOffset", "Date.getTimezoneOffset");
	__hook(Date.prototype, "getUTCDate", "Date.getUTCDate");
	__hook(Date.prototype, "getUTCDay", "Date.getUTCDay");
	__hook(Date.prototype, "getUTCFullYear", "Date.getUTCFullYear");
	__hook(Date.prototype, "getUTCHours", "Date.getUTCHours");
	__hook(Date.prototype, "getUTCMilliseconds", "Date.getUTCMilliseconds");
	__hook(Date.prototype, "getUTCMinutes", "Date.getUTCMinutes");
	__hook(Date.prototype, "getUTCMonth", "Date.getUTCMonth");
	__hook(Date.prototype, "getUTCSeconds", "Date.getUTCSeconds");
	__hook(Date.prototype, "getYear", "Date.getYear");
	__hook(Date.prototype, "setDate", "Date.setDate");
	__hook(Date.prototype, "setFullYear", "Date.setFullYear");
	__hook(Date.prototype, "setHours", "Date.setHours");
	__hook(Date.prototype, "setMilliseconds", "Date.setMilliseconds");
	__hook(Date.prototype, "setMinutes", "Date.setMinutes");
	__hook(Date.prototype, "setMonth", "Date.setMonth");
	__hook(Date.prototype, "setSeconds", "Date.setSeconds");
	__hook(Date.prototype, "setTime", "Date.setTime");
	__hook(Date.prototype, "setUTCDate", "Date.setUTCDate");
	__hook(Date.prototype, "setUTCFullYear", "Date.setUTCFullYear");
	__hook(Date.prototype, "setUTCHours", "Date.setUTCHours");
	__hook(Date.prototype, "setUTCMilliseconds", "Date.setUTCMilliseconds");
	__hook(Date.prototype, "setUTCMinutes", "Date.setUTCMinutes");
	__hook(Date.prototype, "setUTCMonth", "Date.setUTCMonth");
	__hook(Date.prototype, "setUTCSeconds", "Date.setUTCSeconds");
	__hook(Date.prototype, "setYear", "Date.setYear");
	__hook(Date.prototype, "toDateString", "Date.toDateString");
	__hook(Date.prototype, "toISOString", "Date.toISOString");
	__hook(Date.prototype, "toJSON", "Date.toJSON");
	__hook(Date.prototype, "toLocaleString", "Date.toLocaleString");
	__hook(Date.prototype, "toLocaleDateString", "Date.toLocaleDateString");
	__hook(Date.prototype, "toLocaleTimeString", "Date.toLocaleTimeString");
	__hook(Date.prototype, "toString", "Date.toString");
	__hook(Date.prototype, "toTimeString", "Date.toTimeString");
	__hook(Date.prototype, "valueOf", "Date.valueOf");
	__hook(Date, "now", "Date.now");
	__hook(Date, "parse", "Date.parse");
	__hook(Date, "UTC", "Date.UTC");

	__hook(Document.prototype, "adoptNode", "document.adoptNode");
	__hook(
		Document.prototype,
		"addEventListener",
		"document.addEventListener"
	);
	__hook(Document.prototype, "append", "document.append");
	__hook(Document.prototype, "appendChild", "document.appendChild");
	__hook(Document.prototype, "captureEvents", "document.captureEvents");
	__hook(
		Document.prototype,
		"caretPositionFromPoint",
		"document.caretPositionFromPoint"
	);
	__hook(
		Document.prototype,
		"caretRangeFromPoint",
		"document.caretRangeFromPoint"
	);
	__hook(Document.prototype, "clear", "document.clear");
	__hook(Document.prototype, "close", "document.close");
	__hook(
		Document.prototype,
		"createAttribute",
		"document.createAttribute"
	);
	__hook(
		Document.prototype,
		"createAttributeNS",
		"document.createAttributeNS"
	);
	__hook(
		Document.prototype,
		"createCDATASection",
		"document.createCDATASection"
	);
	__hook(Document.prototype, "createComment", "document.createComment");
	__hook(
		Document.prototype,
		"createDocumentFragment",
		"document.createDocumentFragment"
	);
	__hook(Document.prototype, "createEvent", "document.createEvent");
	__hook(Document.prototype, "createElement", "document.createElement");
	__hook(
		Document.prototype,
		"createElementNS",
		"document.createElementNS"
	);
	__hook(
		Document.prototype,
		"createExpression",
		"document.createExpression"
	);
	__hook(
		Document.prototype,
		"createNodeIterator",
		"document.createNodeIterator"
	);
	__hook(
		Document.prototype,
		"createNSResolver",
		"document.createNSResolver"
	);
	__hook(Document.prototype, "createRange", "document.createRange");
	__hook(Document.prototype, "createTextNode", "document.createTextNode");
	__hook(
		Document.prototype,
		"createProcessingInstruction",
		"document.createProcessingInstruction"
	);
	__hook(Document.prototype, "createTouch", "document.createTouch");
	__hook(
		Document.prototype,
		"createTouchList",
		"document.createTouchList"
	);
	__hook(
		Document.prototype,
		"createTreeWalker",
		"document.createTreeWalker"
	);
	__hook(
		Document.prototype,
		"elementFromPoint",
		"document.elementFromPoint"
	);
	__hook(
		Document.prototype,
		"elementsFromPoint",
		"document.elementsFromPoint"
	);
	__hook(
		Document.prototype,
		"enableStyleSheetsForSet",
		"document.enableStyleSheetsForSet"
	);
	__hook(Document.prototype, "evaluate", "document.evaluate");
	__hook(Document.prototype, "execCommand", "document.execCommand");
	__hook(Document.prototype, "exitFullScreen", "document.exitFullScreen");
	__hook(
		Document.prototype,
		"exitPictureInPicture",
		"document.exitPictureInPicture"
	);
	__hook(
		Document.prototype,
		"exitPointerLock",
		"document.exitPointerLock"
	);
	__hook(Document.prototype, "getAnimations", "document.getAnimations");
	__hook(Document.prototype, "getElementById", "document.getElementById");
	__hook(
		Document.prototype,
		"getElementsByClassName",
		"document.getElementsByClassName"
	);
	__hook(
		Document.prototype,
		"getElementsByName",
		"document.getElementsByName"
	);
	__hook(
		Document.prototype,
		"getElementsByTagName",
		"document.getElementsByTagName"
	);
	__hook(
		Document.prototype,
		"getElementsByTagNameNS",
		"document.getElementsByTagNameNS"
	);
	__hook(Document.prototype, "getSelection", "document.getSelection");
	__hook(Document.prototype, "hasFocus", "document.hasFocus");
	__hook(
		Document.prototype,
		"hasStorageAccess",
		"document.hasStorageAccess"
	);
	__hook(Document.prototype, "importNode", "document.importNode");
	__hook(Document.prototype, "open", "document.open");
	__hook(Document.prototype, "prepend", "document.prepend");
	__hook(
		Document.prototype,
		"queryCommandEnabled",
		"document.queryCommandEnabled"
	);
	__hook(
		Document.prototype,
		"queryCommandState",
		"document.queryCommandState"
	);
	__hook(
		Document.prototype,
		"queryCommandSupported",
		"document.queryCommandSupported"
	);
	__hook(Document.prototype, "querySelector", "document.querySelector");
	__hook(
		Document.prototype,
		"querySelectorAll",
		"document.querySelectorAll"
	);
	__hook(Document.prototype, "releaseCapture", "document.releaseCapture");
	__hook(
		Document.prototype,
		"replaceChildren",
		"document.replaceChildren"
	);
	__hook(
		Document.prototype,
		"requestStorageAccess",
		"document.requestStorageAccess"
	);
	__hook(
		Document.prototype,
		"startViewTransition",
		"document.startViewTransition"
	);
	__hook(Document.prototype, "write", "document.write");
	__hook(Document.prototype, "writeln", "document.writeln");

	__hook(Function.prototype, "bind", "Function.bind");
	__hook(Function.prototype, "toString", "Function.toString");

	__hook(
		EventTarget.prototype,
		"addEventListener",
		"EventTarget.addEventListener"
	);
	__hook(
		EventTarget.prototype,
		"dispatchEvent",
		"EventTarget.dispatchEvent"
	);
	__hook(
		EventTarget.prototype,
		"removeEventListener",
		"EventTarget.removeEventListener"
	);

	__hook(History.prototype, "back", "History.back");
	__hook(History.prototype, "forward", "History.forward");
	__hook(History.prototype, "go", "History.go");
	__hook(History.prototype, "pushState", "History.pushState");
	__hook(History.prototype, "replaceState", "History.replaceState");

	__hook(IDBFactory.prototype, "cmp", "IndexedDB.cmp");
	__hook(IDBFactory.prototype, "databases", "IndexedDB.databases");
	__hook(
		IDBFactory.prototype,
		"deleteDatabase",
		"IndexedDB.deleteDatabase"
	);
	__hook(IDBFactory.prototype, "open", "IndexedDB.open");
	__hook(IDBDatabase.prototype, "close", "IndexedDB.close");
	__hook(
		IDBDatabase.prototype,
		"createObjectStore",
		"IndexedDB.createObjectStore"
	);
	__hook(
		IDBDatabase.prototype,
		"deleteObjectStore",
		"IndexedDB.deleteObjectStore"
	);
	__hook(IDBDatabase.prototype, "transaction", "IndexedDB.transaction");
	__hook(IDBTransaction.prototype, "abort", "IndexedDB.open");
	__hook(IDBTransaction.prototype, "commit", "IndexedDB.commit");
	__hook(
		IDBTransaction.prototype,
		"objectStore",
		"IndexedDB.objectStore"
	);
	__hook(IDBObjectStore.prototype, "add", "IndexedDB.add");
	__hook(IDBObjectStore.prototype, "clear", "IndexedDB.clear");
	__hook(IDBObjectStore.prototype, "count", "IndexedDB.count");
	__hook(
		IDBObjectStore.prototype,
		"createIndex",
		"IndexedDB.createIndex"
	);
	__hook(IDBObjectStore.prototype, "delete", "IndexedDB.delete");
	__hook(
		IDBObjectStore.prototype,
		"deleteIndex",
		"IndexedDB.deleteIndex"
	);
	__hook(IDBObjectStore.prototype, "get", "IndexedDB.get");
	__hook(IDBObjectStore.prototype, "getAll", "IndexedDB.getAll");
	__hook(IDBObjectStore.prototype, "getAllKeys", "IndexedDB.getAllKeys");
	__hook(IDBObjectStore.prototype, "getKey", "IndexedDB.getKey");
	__hook(IDBObjectStore.prototype, "index", "IndexedDB.index");
	__hook(IDBObjectStore.prototype, "openCursor", "IndexedDB.openCursor");
	__hook(
		IDBObjectStore.prototype,
		"openKeyCursor",
		"IndexedDB.openKeyCursor"
	);
	__hook(IDBObjectStore.prototype, "put", "IndexedDB.put");
	__hook(IDBCursor.prototype, "advance", "IndexedDB.advance");
	__hook(IDBCursor.prototype, "continue", "IndexedDB.continue");
	__hook(
		IDBCursor.prototype,
		"continuePrimaryKey",
		"IndexedDB.continuePrimaryKey"
	);
	__hook(IDBCursor.prototype, "delete", "IndexedDB.delete");
	__hook(IDBCursor.prototype, "update", "IndexedDB.update");
	__hook(IDBKeyRange.prototype, "bound", "IndexedDB.bound");
	__hook(IDBKeyRange.prototype, "lowerBound", "IndexedDB.lowerBound");
	__hook(IDBKeyRange.prototype, "only", "IndexedDB.only");
	__hook(IDBKeyRange.prototype, "upperBound", "IndexedDB.upperBound");

	__hook(JSON, "parse", "JSON.parse");
	__hook(JSON, "stringify", "JSON.stringify");

	__hook(Math, "abs", "Math.abs");
	__hook(Math, "acos", "Math.acos");
	__hook(Math, "acosh", "Math.acosh");
	__hook(Math, "asin", "Math.asin");
	__hook(Math, "asinh", "Math.asinh");
	__hook(Math, "atan", "Math.atan");
	__hook(Math, "atan2", "Math.atan2");
	__hook(Math, "atanh", "Math.atanh");
	__hook(Math, "cbrt", "Math.cbrt");
	__hook(Math, "ceil", "Math.ceil");
	__hook(Math, "clz32", "Math.clz32");
	__hook(Math, "cos", "Math.cos");
	__hook(Math, "cosh", "Math.cosh");
	__hook(Math, "exp", "Math.exp");
	__hook(Math, "expm1", "Math.expm1");
	__hook(Math, "floor", "Math.floor");
	__hook(Math, "fround", "Math.fround");
	__hook(Math, "hypot", "Math.hypot");
	__hook(Math, "imul", "Math.imul");
	__hook(Math, "log", "Math.log");
	__hook(Math, "log10", "Math.log10");
	__hook(Math, "log1p", "Math.log1p");
	__hook(Math, "log2", "Math.log2");
	__hook(Math, "max", "Math.max");
	__hook(Math, "min", "Math.min");
	__hook(Math, "pow", "Math.pow");
	__hook(Math, "random", "Math.random");
	__hook(Math, "round", "Math.round");
	__hook(Math, "sign", "Math.sign");
	__hook(Math, "sin", "Math.sin");
	__hook(Math, "sinh", "Math.sinh");
	__hook(Math, "sqrt", "Math.sqrt");
	__hook(Math, "tan", "Math.tan");
	__hook(Math, "tanh", "Math.tanh");
	__hook(Math, "trunc", "Math.trunc");

	if (navigator.canShare)
		__hook(navigator, "canShare", "navigator.canShare");
	if (navigator.clearAppBadge)
		__hook(navigator, "clearAppBadge", "navigator.clearAppBadge");
	if (navigator.getAutoplayPolicy)
		__hook(navigator, "getAutoplayPolicy", "navigator.getAutoplayPolicy");
	if (navigator.getBattery)
		__hook(navigator, "getBattery", "navigator.getBattery");
	__hook(navigator, "getGamepads", "navigator.getGamepads");
	if (navigator.getInstalledRelatedApps)
		__hook(
			navigator,
			"getInstalledRelatedApps",
			"navigator.getInstalledRelatedApps"
		);
	if (navigator.getUserMedia)
		__hook(navigator, "getUserMedia", "navigator.getUserMedia");
	if (navigator.getVRDisplays)
		__hook(navigator, "getVRDisplays", "navigator.getVRDisplays");
	__hook(navigator, "javaEnabled", "navigator.javaEnabled");
	if (navigator.registerProtocolHandler)
		__hook(
			navigator,
			"registerProtocolHandler",
			"navigator.registerProtocolHandler"
		);
	if (navigator.requestMediaKeySystemAccess)
		__hook(
			navigator,
			"requestMediaKeySystemAccess",
			"navigator.requestMediaKeySystemAccess"
		);
	if (navigator.requestMIDIAccess)
		__hook(navigator, "requestMIDIAccess", "navigator.requestMIDIAccess");
	if (navigator.share) __hook(navigator, "share", "navigator.share");
	if (navigator.taintEnabled)
		__hook(navigator, "taintEnabled", "navigator.taintEnabled");
	if (navigator.unregisterProtocolHandler)
		__hook(
			navigator,
			"unregisterProtocolHandler",
			"navigator.unregisterProtocolHandler"
		);
	__hook(navigator, "vibrate", "navigator.vibrate");

	if (navigator.clipboard) {
		__hook(navigator.clipboard, "read", "navigator.clipboard.read");
		__hook(
			navigator.clipboard,
			"readText",
			"navigator.clipboard.readText"
		);
		__hook(navigator.clipboard, "write", "navigator.clipboard.write");
		__hook(
			navigator.clipboard,
			"writeText",
			"navigator.clipboard.writeText"
		);
	}

	__hook(
		navigator.geolocation,
		"clearWatch",
		"navigator.geolocation.clearWatch"
	);
	__hook(
		navigator.geolocation,
		"getCurrentPosition",
		"navigator.geolocation.getCurrentPosition"
	);
	__hook(
		navigator.geolocation,
		"watchPosition",
		"navigator.geolocation.watchPosition"
	);

	if (navigator.mediaCapabilities) {
		__hook(
			navigator.mediaCapabilities,
			"decodingInfo",
			"navigator.mediaCapabilities.decodingInfo"
		);
		__hook(
			navigator.mediaCapabilities,
			"encodingInfo",
			"navigator.mediaCapabilities.encodingInfo"
		);
	}

	__hook(navigator.permissions, "query", "navigator.permissions.query");
	__hook(navigator.permissions, "revoke", "navigator.permissions.revoke");

	if (navigator.userAgentData) {
		__hook(
			navigator.userAgentData,
			"getHighEntropyValues",
			"navigator.userAgentData.getHighEntropyValues"
		);
		__hook(
			navigator.userAgentData,
			"toJSON",
			"navigator.userAgentData.toJSON"
		);
	}

	if (navigator.serviceWorker) {
		__hook(
			navigator.serviceWorker,
			"getRegistration",
			"navigator.serviceWorker.getRegistration"
		);
		__hook(
			navigator.serviceWorker,
			"getRegistrations",
			"navigator.serviceWorker.getRegistrations"
		);
		__hook(
			navigator.serviceWorker,
			"register",
			"navigator.serviceWorker.register"
		);
		__hook(
			navigator.serviceWorker,
			"startMessages",
			"navigator.serviceWorker.startMessages"
		);
	}
	if (navigator.storage) {
		__hook(navigator.storage, "estimate", "navigator.storage.estimate");
		__hook(
			navigator.storage,
			"getDirectory",
			"navigator.storage.getDirectory"
		);
		__hook(navigator.storage, "persist", "navigator.storage.persist");
		__hook(navigator.storage, "persisted", "navigator.storage.persisted");
	}

	__hook(
		navigator.scheduling,
		"isInputPending",
		"navigator.scheduling.isInputPending"
	);

	__hook(Node.prototype, "appendChild", "Node.appendChild");
	__hook(Node.prototype, "cloneNode", "Node.cloneNode");
	__hook(
		Node.prototype,
		"compareDocumentPosition",
		"Node.compareDocumentPosition"
	);
	__hook(Node.prototype, "contains", "Node.contains");
	__hook(Node.prototype, "getRootNode", "Node.getRootNode");
	__hook(Node.prototype, "hasChildNodes", "Node.hasChildNodes");
	__hook(Node.prototype, "insertBefore", "Node.insertBefore");
	__hook(Node.prototype, "isDefaultNamespace", "Node.isDefaultNamespace");
	__hook(Node.prototype, "isEqualNode", "Node.isEqualNode");
	__hook(Node.prototype, "isSameNode", "Node.isSameNode");
	__hook(Node.prototype, "lookupNamespaceURI", "Node.lookupNamespaceURI");
	__hook(Node.prototype, "lookupPrefix", "Node.lookupPrefix");
	__hook(Node.prototype, "normalize", "Node.normalize");
	__hook(Node.prototype, "removeChild", "Node.removeChild");
	__hook(Node.prototype, "replaceChild", "Node.replaceChild");

	__hook(Number, "isFinite", "Number.isFinite");
	__hook(Number, "isInteger", "Number.isInteger");
	__hook(Number, "isNan", "Number.isNan");
	__hook(Number, "isSafeInteger", "Number.isSafeInteger");
	__hook(Number, "parseFloat", "Number.parseFloat");
	__hook(Number, "parseInt", "Number.parseInt");
	__hook(Number.prototype, "toExponential", "Number.toExponential");
	__hook(Number.prototype, "toFixed", "Number.toFixed");
	__hook(Number.prototype, "toLocaleString", "Number.toLocaleString");
	__hook(Number.prototype, "toPrecision", "Number.toPrecision");
	__hook(Number.prototype, "toString", "Number.toString");
	__hook(Number.prototype, "valueOf", "Number.valueOf");

	__hook(Object, "assign", "Object.assign");
	__hook(Object, "create", "Object.create");
	__hook(Object, "defineProperties", "Object.defineProperties");
	__hook(Object, "defineProperty", "Object.defineProperty");
	__hook(Object, "entries", "Object.entries");
	__hook(Object, "freeze", "Object.freeze");
	__hook(Object, "fromEntries", "Object.fromEntries");
	__hook(
		Object,
		"getOwnPropertyDescriptor",
		"Object.getOwnPropertyDescriptor"
	);
	__hook(
		Object,
		"getOwnPropertyDescriptors",
		"Object.getOwnPropertyDescriptors"
	);
	__hook(Object, "getOwnPropertyNames", "Object.getOwnPropertyNames");
	__hook(Object, "getOwnPropertySymbols", "Object.getOwnPropertySymbols");
	__hook(Object, "getPrototypeOf", "Object.getPrototypeOf");
	__hook(Object, "hasOwn", "Object.hasOwn");
	__hook(Object, "is", "Object.is");
	__hook(Object, "isExtensible", "Object.isExtensible");
	__hook(Object, "isFrozen", "Object.isFrozen");
	__hook(Object, "isSealed", "Object.isSealed");
	__hook(Object, "keys", "Object.keys");
	__hook(Object, "preventExtensions", "Object.preventExtensions");
	__hook(Object, "seal", "Object.seal");
	__hook(Object, "setPrototypeOf", "Object.setPrototypeOf");
	__hook(Object, "values", "Object.values");
	__hook(Object.prototype, "__defineGetter__", "Object.__defineGetter__");
	__hook(Object.prototype, "__defineSetter__", "Object.__defineSetter__");
	__hook(Object.prototype, "__lookupGetter__", "Object.__lookupGetter__");
	__hook(Object.prototype, "__lookupSetter__", "Object.__lookupSetter__");
	__hook(Object.prototype, "hasOwnProperty", "Object.hasOwnProperty");
	__hook(Object.prototype, "isPrototypeOf", "Object.isPrototypeOf");
	__hook(
		Object.prototype,
		"propertyIsEnumerable",
		"Object.propertyIsEnumerable"
	);
	__hook(Object.prototype, "toLocaleString", "Object.toLocaleString");
	__hook(Object.prototype, "toString", "Object.toString");
	__hook(Object.prototype, "valueOf", "Object.valueOf");

	__hook(RegExp.prototype, "compile", "RegExp.compile");
	__hook(RegExp.prototype, "exec", "RegExp.exec");
	__hook(RegExp.prototype, "toString", "RegExp.toString");
	__hook(RegExp.prototype, "test", "RegExp.test");

	__hook(Reflect, "apply", "Reflect.apply");
	__hook(Reflect, "construct", "Reflect.construct");
	__hook(Reflect, "defineProperty", "Reflect.defineProperty");
	__hook(Reflect, "deleteProperty", "Reflect.deleteProperty");
	__hook(Reflect, "get", "Reflect.get");
	__hook(
		Reflect,
		"getOwnPropertyDescriptor",
		"Reflect.getOwnPropertyDescriptor"
	);
	__hook(Reflect, "getPrototypeOf", "Reflect.getPrototypeOf");
	__hook(Reflect, "has", "Reflect.has");
	__hook(Reflect, "isExtensible", "Reflect.isExtensible");
	__hook(Reflect, "ownKeys", "Reflect.ownKeys");
	__hook(Reflect, "preventExtensions", "Reflect.preventExtensions");
	__hook(Reflect, "set", "Reflect.set");
	__hook(Reflect, "setPrototypeOf", "Reflect.setPrototypeOf");

	__hook(Set.prototype, "add", "Set.add");
	__hook(Set.prototype, "clear", "Set.clear");
	__hook(Set.prototype, "delete", "Set.delete");
	__hook(Set.prototype, "entries", "Set.entries");
	__hook(Set.prototype, "forEach", "Set.forEach");
	__hook(Set.prototype, "has", "Set.has");
	__hook(Set.prototype, "keys", "Set.keys");
	__hook(Set.prototype, "values", "Set.values");

	__hook(String, "raw", "String.raw");
	__hook(String, "fromCharCode", "String.fromCharCode");
	__hook(String, "fromCodePoint", "String.fromCodePoint");

	__hook(String.prototype, "anchor", "String.anchor");
	__hook(String.prototype, "at", "String.at");
	__hook(String.prototype, "big", "String.big");
	__hook(String.prototype, "blink", "String.blink");
	__hook(String.prototype, "bold", "String.bold");
	__hook(String.prototype, "charAt", "String.charAt");
	__hook(String.prototype, "charCodeAt", "String.charCodeAt");
	__hook(String.prototype, "codePointAt", "String.codePointAt");
	__hook(String.prototype, "concat", "String.concat");
	__hook(String.prototype, "endsWith", "String.endsWith");
	__hook(String.prototype, "fixed", "String.fixed");
	__hook(String.prototype, "fontcolor", "String.fontcolor");
	__hook(String.prototype, "fontsize", "String.fontsize");
	__hook(String.prototype, "includes", "String.includes");
	__hook(String.prototype, "indexOf", "String.indexOf");
	__hook(String.prototype, "isWellFormed", "String.isWellFormed");
	__hook(String.prototype, "italics", "String.italics");
	__hook(String.prototype, "lastIndexOf", "String.lastIndexOf");
	__hook(String.prototype, "link", "String.link");
	__hook(String.prototype, "localeCompare", "String.localeCompare");
	__hook(String.prototype, "match", "String.match");
	__hook(String.prototype, "matchAll", "String.matchAll");
	__hook(String.prototype, "normalize", "String.normalize");
	__hook(String.prototype, "padStart", "String.padStart");
	__hook(String.prototype, "repeat", "String.repeat");
	__hook(String.prototype, "replace", "String.replace");
	__hook(String.prototype, "replaceAll", "String.replaceAll");
	__hook(String.prototype, "search", "String.search");
	__hook(String.prototype, "slice", "String.slice");
	__hook(String.prototype, "small", "String.small");
	__hook(String.prototype, "split", "String.split");
	__hook(String.prototype, "startsWith", "String.startsWith");
	__hook(String.prototype, "strike", "String.strike");
	__hook(String.prototype, "sub", "String.sub");
	__hook(String.prototype, "substr", "String.substr");
	__hook(String.prototype, "substring", "String.substring");
	__hook(String.prototype, "sup", "String.sup");
	__hook(String.prototype, "toLocaleString", "String.toLocaleString");
	__hook(
		String.prototype,
		"toLocaleLowerCase",
		"String.toLocaleLowerCase"
	);
	__hook(
		String.prototype,
		"toLocaleUpperCase",
		"String.toLocaleUpperCase"
	);
	__hook(String.prototype, "toLowerCase", "String.toLowerCase");
	__hook(String.prototype, "toUpperCase", "String.toUpperCase");
	__hook(String.prototype, "toWellFormed", "String.toWellFormed");
	__hook(String.prototype, "trim", "String.trim");
	__hook(String.prototype, "trimEnd", "String.trimEnd");
	__hook(String.prototype, "trimStart", "String.trimStart");
	__hook(String.prototype, "valueOf", "String.valueOf");

	__hook(Symbol, "for", "Symbol.for");
	__hook(Symbol, "keyFor", "Symbol.keyFor");
	__hook(Symbol.prototype, "valueOf", "Symbol.valueOf");
	__hook(Symbol.prototype, "toString", "Symbol.toString");

	if (window.SubtleCrypto) {
		__hook(SubtleCrypto.prototype, "encrypt", "SubtleCrypto.encrypt");
		__hook(SubtleCrypto.prototype, "decrypt", "SubtleCrypto.decrypt");
		__hook(SubtleCrypto.prototype, "sign", "SubtleCrypto.sign");
		__hook(SubtleCrypto.prototype, "verify", "SubtleCrypto.verify");
		__hook(SubtleCrypto.prototype, "digest", "SubtleCrypto.digest");
		__hook(
			SubtleCrypto.prototype,
			"generateKey",
			"SubtleCrypto.generateKey"
		);
		__hook(
			SubtleCrypto.prototype,
			"deriveBits",
			"SubtleCrypto.deriveBits"
		);
		__hook(SubtleCrypto.prototype, "importKey", "SubtleCrypto.importKey");
		__hook(SubtleCrypto.prototype, "exportKey", "SubtleCrypto.exportKey");
		__hook(SubtleCrypto.prototype, "wrapKey", "SubtleCrypto.wrapKey");
		__hook(SubtleCrypto.prototype, "unwrapKey", "SubtleCrypto.unwrapKey");
	}

	__hook(Map.prototype, "get", "Map.get");
	__hook(Map.prototype, "set", "Map.set");
	__hook(Map.prototype, "delete", "Map.delete");
	__hook(Map.prototype, "has", "Map.has");
	__hook(Map.prototype, "values", "Map.values");
	__hook(Map.prototype, "entries", "Map.entries");
	__hook(Map.prototype, "clear", "Map.clear");
	__hook(Map.prototype, "keys", "Map.keys");
	__hook(Map.prototype, "forEach", "Map.forEach");

	__hook(WeakMap.prototype, "get", "WeakMap.get");
	__hook(WeakMap.prototype, "set", "WeakMap.set");
	__hook(WeakMap.prototype, "delete", "WeakMap.delete");
	__hook(WeakMap.prototype, "has", "WeakMap.has");

	__hook(WeakSet.prototype, "add", "WeakSet.add");
	__hook(WeakSet.prototype, "delete", "WeakSet.delete");
	__hook(WeakSet.prototype, "has", "WeakSet.has");

	__hook(window, "fetch", "fetch");
	__hook(window, "isFinite", "window.isFinite");
	__hook(window, "isNaN", "window.isNaN");
	__hook(window, "parseFloat", "window.parseFloat");
	__hook(window, "parseInt", "window.parseInt");
	__hook(window, "decodeURI", "window.decodeURI");
	__hook(window, "decodeURIComponent", "window.decodeURIComponent");
	__hook(window, "encodeURI", "window.encodeURI");
	__hook(window, "encodeURIComponent", "window.encodeURIComponent");
	__hook(window, "escape", "window.escape");
	__hook(window, "unescape", "window.unescape");
	__hook(window, "alert", "window.alert");
	__hook(window, "back", "window.back");
	__hook(window, "blur", "window.blur");
	__hook(window, "cancelAnimationFrame", "window.cancelAnimationFrame");
	__hook(window, "cancelIdleCallback", "window.cancelIdleCallback");
	__hook(window, "captureEvents", "window.captureEvents");
	__hook(window, "clearImmediate", "window.clearImmediate");
	__hook(window, "close", "window.close");
	__hook(window, "confirm", "window.confirm");
	__hook(
		window,
		"convertPointFromNodeToPage",
		"window.convertPointFromNodeToPage"
	);
	__hook(window, "dump", "window.dump");
	__hook(window, "find", "window.find");
	__hook(window, "focus", "window.focus");
	__hook(window, "forward", "window.forward");
	__hook(window, "getComputedStyle", "window.getComputedStyle");
	__hook(
		window,
		"getDefaultComputedStyle",
		"window.getDefaultComputedStyle"
	);
	__hook(window, "getSelection", "window.getSelection");
	__hook(window, "matchMedia", "window.matchMedia");
	__hook(window, "moveBy", "window.moveBy");
	__hook(window, "moveTo", "window.moveTo");
	__hook(window, "open", "window.open");
	__hook(window, "postMessage", "window.postMessage");
	__hook(window, "print", "window.print");
	__hook(window, "prompt", "window.prompt");
	__hook(window, "queryLocalFonts", "window.queryLocalFonts");
	__hook(window, "releaseEvents", "window.releaseEvents");

	__hook(window, "requestAnimationFrame", "window.requestAnimationFrame");
	__hook(window, "requestFileSystem", "window.requestFileSystem");
	__hook(window, "requestIdleCallback", "window.requestIdleCallback");
	__hook(window, "resizeBy", "window.resizeBy");
	__hook(window, "resizeTo", "window.resizeTo");
	__hook(window, "scroll", "window.scroll");
	__hook(window, "scrollBy", "window.scrollBy");
	__hook(window, "scrollByLines", "window.scrollByLines");
	__hook(window, "scrollByPages", "window.scrollBy");
	__hook(window, "scrollTo", "window.scrollTo");
	__hook(window, "setImmediate", "window.setImmediate");
	__hook(window, "setTimeout", "window.setTimeout");
	__hook(window, "setInterval", "window.setInterval");
	__hook(window, "showDirectoryPicker", "window.showDirectoryPicker");
	__hook(window, "showModalDialog", "window.showModalDialog");
	__hook(window, "showOpenFilePicker", "window.showOpenFilePicker");
	__hook(window, "showSaveFilePicker", "window.showSaveFilePicker");
	__hook(window, "stop", "window.stop");
	__hook(window, "updateCommands", "window.updateCommands");
	__hook(
		window,
		"webkitConvertPointFromPageToNode",
		"window.webkitConvertPointFromPageToNode"
	);

	__hook(Element.prototype, "after", "Element.after");
	__hook(Element.prototype, "animate", "Element.animate");
	__hook(Element.prototype, "append", "Element.append");
	__hook(Element.prototype, "attachShadow", "Element.attachShadow");
	__hook(Element.prototype, "before", "Element.before");
	__hook(Element.prototype, "checkVisibility", "Element.checkVisibility");
	__hook(Element.prototype, "closest", "Element.closest");
	__hook(
		Element.prototype,
		"computedStyleMap",
		"Element.computedStyleMap"
	);
	__hook(Element.prototype, "getAnimations", "Element.getAnimations");
	__hook(Element.prototype, "getAttribute", "Element.getAttribute");
	__hook(
		Element.prototype,
		"getAttributeNames",
		"Element.getAttributeNames"
	);
	__hook(
		Element.prototype,
		"getAttributeNode",
		"Element.getAttributeNode"
	);
	__hook(
		Element.prototype,
		"getAttributeNodeNS",
		"Element.getAttributeNodeNS"
	);
	__hook(Element.prototype, "getAttributeNS", "Element.getAttributeNS");
	__hook(
		Element.prototype,
		"getBoundingClientRect",
		"Element.getBoundingClientRect"
	);
	__hook(Element.prototype, "getClientRects", "Element.getClientRects");
	__hook(
		Element.prototype,
		"getElementsByClassName",
		"Element.getElementsByClassName"
	);
	__hook(
		Element.prototype,
		"getElementsByTagName",
		"Element.getElementsByTagName"
	);
	__hook(
		Element.prototype,
		"getElementsByTagNameNS",
		"Element.getElementsByTagNameNS"
	);
	__hook(Element.prototype, "hasAttribute", "Element.hasAttribute");
	__hook(Element.prototype, "hasAttributeNS", "Element.hasAttributeNS");
	__hook(Element.prototype, "hasAttributes", "Element.hasAttributes");
	__hook(
		Element.prototype,
		"hasPointerCapture",
		"Element.hasPointerCapture"
	);
	__hook(
		Element.prototype,
		"insertAdjacentElement",
		"Element.insertAdjacentElement"
	);
	__hook(
		Element.prototype,
		"insertAdjacentHTML",
		"Element.insertAdjacentHTML"
	);
	__hook(
		Element.prototype,
		"insertAdjacentText",
		"Element.insertAdjacentText"
	);
	__hook(Element.prototype, "matches", "Element.matches");
	__hook(Element.prototype, "prepend", "Element.prepend");
	__hook(Element.prototype, "querySelector", "Element.querySelector");
	__hook(
		Element.prototype,
		"querySelectorAll",
		"Element.querySelectorAll"
	);
	__hook(
		Element.prototype,
		"releasePointerCapture",
		"Element.releasePointerCapture"
	);
	__hook(Element.prototype, "remove", "Element.remove");
	__hook(Element.prototype, "removeAttribute", "Element.removeAttribute");
	__hook(
		Element.prototype,
		"removeAttributeNode",
		"Element.removeAttributeNode"
	);
	__hook(
		Element.prototype,
		"removeAttributeNS",
		"Element.removeAttributeNS"
	);
	__hook(Element.prototype, "replaceChildren", "Element.replaceChildren");
	__hook(Element.prototype, "replaceWith", "Element.replaceWith");
	__hook(
		Element.prototype,
		"requestFullscreen",
		"Element.requestFullscreen"
	);
	__hook(
		Element.prototype,
		"requestPointerLock",
		"Element.requestPointerLock"
	);
	__hook(Element.prototype, "scroll", "Element.scroll");
	__hook(Element.prototype, "scrollBy", "Element.scrollBy");
	__hook(Element.prototype, "scrollIntoView", "Element.scrollIntoView");
	__hook(
		Element.prototype,
		"scrollIntoViewIfNeeded",
		"Element.scrollIntoViewIfNeeded"
	);
	__hook(Element.prototype, "scrollTo", "Element.scrollTo");
	__hook(Element.prototype, "setAttribute", "Element.setAttribute");
	__hook(
		Element.prototype,
		"setAttributeNode",
		"Element.setAttributeNode"
	);
	__hook(
		Element.prototype,
		"setAttributeNodeNS",
		"Element.setAttributeNodeNS"
	);
	__hook(Element.prototype, "setAttributeNS", "Element.setAttributeNS");
	__hook(Element.prototype, "setCapture", "Element.setCapture");
	__hook(Element.prototype, "setHTML", "Element.setHTML");
	__hook(
		Element.prototype,
		"setPointerCapture",
		"Element.setPointerCapture"
	);
	__hook(Element.prototype, "toggleAttribute", "Element.toggleAttribute");

	__hook(XMLHttpRequest.prototype, "abort", "XMLHttpRequest.abort");
	__hook(
		XMLHttpRequest.prototype,
		"addEventListener",
		"XMLHttpRequest.addEventListener"
	);
	__hook(
		XMLHttpRequest.prototype,
		"dispatchEvent",
		"XMLHttpRequest.dispatchEvent"
	);
	__hook(
		XMLHttpRequest.prototype,
		"removeEventListener",
		"XMLHttpRequest.removeEventListener"
	);

	__hook(
		XMLHttpRequest.prototype,
		"overrideMimeType",
		"XMLHttpRequest.overrideMimeType"
	);
	__hook(
		XMLHttpRequest.prototype,
		"getAllResponseHeaders",
		"XMLHttpRequest.getAllResponseHeaders"
	);
	__hook(
		XMLHttpRequest.prototype,
		"getResponseHeader",
		"XMLHttpRequest.getResponseHeader"
	);
	__hook(XMLHttpRequest.prototype, "open", "XMLHttpRequest.open");
	__hook(XMLHttpRequest.prototype, "send", "XMLHttpRequest.send");
	__hook(
		XMLHttpRequest.prototype,
		"setRequestHeader",
		"XMLHttpRequest.setRequestHeader"
	);

	if (window.TrustedTypePolicyFactory) {
		__hook(
			TrustedTypePolicyFactory.prototype,
			"createPolicy",
			"TrustedTypePolicyFactory.createPolicy"
		);
		__hook(
			TrustedTypePolicyFactory.prototype,
			"getAttributeType",
			"TrustedTypePolicyFactory.getAttributeType"
		);
		__hook(
			TrustedTypePolicyFactory.prototype,
			"getPropertyType",
			"TrustedTypePolicyFactory.getPropertyType"
		);
		__hook(
			TrustedTypePolicyFactory.prototype,
			"isHTML",
			"TrustedTypePolicyFactory.isHTML"
		);
		__hook(
			TrustedTypePolicyFactory.prototype,
			"isScript",
			"TrustedTypePolicyFactory.isScript"
		);
		__hook(
			TrustedTypePolicyFactory.prototype,
			"isScriptURL",
			"TrustedTypePolicyFactory.isScriptURL"
		);
	}
})();

// Event-based Hooks
(() => {
	// Message Interceptor
	window.__addEventListener("message", (event) => {
		if (
			event.data == null ||
			event.data === "" ||
			event.data === "pmz27qdv8gr2ah5doq632jdcie4rc2cr" ||
			(event.data?.swag && event.data?.swag === "DNT")
		)
			return;
		let source = "";
		try {
			source = event.source.location.href;
		} catch (e) { }
		__dispatchPollData({
			type: "message",
			stage: "intercept",
			message: event.data,
			source,
			target: event.target.location.href,
			origin: event.origin,
			url: window.top.location.href,
		}, stage);
	});

	//Client-side storage state on before page load.
	window.__addEventListener("DOMContentLoaded", async function (e) {
		await __pollStorage("DOMContentLoaded");
	});

	//Client-side storage state on before page unload.
	window.__addEventListener("beforeunload", async function (e) {
		await __pollStorage("beforeunload");
	});
})();
