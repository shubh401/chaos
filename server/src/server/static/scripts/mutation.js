(() => {
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
				return value.toString();
			}
			if (typeof value === "function") {
				return Function.prototype.toString(value);
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
			if (value instanceof BigInt) {
				return value.toLocaleString();
			}
			if (ancestors.has(value)) {
				return "[Circular]";
			}
			ancestors.add(value);
			return value;
		};
	};

	window.__dispatchMutationData = async function (data) {
		let parsed_data;
		try {
			parsed_data = JSON.stringify.apply(this, [
				{
					type: "mutation",
					data,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					url: window.location.href,
					contextURL: document.location.href,
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer(),
			]);
			fetch(`${location.origin}${window.location.pathname}mutation`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: parsed_data,
			});
		} catch (e) {
			window.__dispatchErrorLog(
				{
					type: window.top.location.search,
					source: "__dispatchMutationData",
					error: { stack: e.stack, message: e.message, name: e.name },
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				});
		}
	};

	window.__dispatchErrorLog = async function (data) {
		let parsed_data;
		try {
			parsed_data = JSON.stringify(data, window.__getCircularReplacer());
			window.fetch(`${location.origin}${window.location.pathname}error`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: parsed_data,
			});
		} catch (e) {
			console.error(data);
		}
	};

	window.__extractNodeInfo = function (node, isSibling = false) {
		try {
			let data = {};
			data["name"] = node.nodeName;
			if (
				node.innerText?.includes("_storageProxy") ||
				node.innerText?.includes("__hookProperty") ||
				node.innerText?.includes(
					"function __hook(object, property, tag)"
				) ||
				node.innerText?.includes(
					'var extensionId = new URLSearchParams(window.location.search).get("extensionId");'
				)
			)
				return undefined;
			data["innerText"] = node.innerText;
			if (!isSibling) {
				data["src"] = node.src;
				data["type"] = node.type;
			}
			data["isConnected"] = node.isConnected;
			return data;
		} catch (e) {
			window.__dispatchErrorLog(
				{
					type: window.top.location.search,
					source: "__extractNodeInfo",
					error: { stack: e.stack, message: e.message, name: e.name },
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				});
		}
	};

	window.__processNodeList = function (nodeList) {
		try {
			if (nodeList === undefined || nodeList.length === 0) return undefined;
			let nodeListData = [];
			try {
				nodeList.forEach((node) => {
					let nodeData = window.__extractNodeInfo(node);
					if (nodeData) {
						if (nodeData.innerText)
							nodeData.hash = SparkMD5.hash(nodeData.innerText).toString();
						else {
							nodeData.hash = SparkMD5.hash(JSON.stringify(nodeData));
						}
						if (!__knownHashes.has(nodeData.hash)) {
							nodeListData.push(nodeData);
							__knownHashes.add(nodeData.hash);
						}
					}
				});
			} catch (e) {
				console.error("__processNodeList", e);
			} finally {
				return nodeListData;
			}
		} catch (e) {
			window.__dispatchErrorLog(
				{
					type: window.top.location.search,
					source: "__processNodeList",
					error: { stack: e.stack, message: e.message, name: e.name },
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				});
		}
	};

	window.__processMutationTarget = function (target, type) {
		try {
			let targetData;
			if (type === "childList") {
				targetData = window.__extractNodeInfo(target);
			} else if (type === "attributes") {
				let attrs = [];
				[...target.attributes].forEach((a) => {
					attrs.push(`${a.nodeName}=${a.nodeValue}`);
				});
				targetData = {
					id: target.id,
					attrs,
					classList: Array.from(target.classList),
					tagName: target.tagName,
				};
			} else if (type === "characterData") {
				targetData = {
					value: target.data,
					length: target.length,
				};
			}
			return targetData;
		} catch (e) {
			window.__dispatchErrorLog(
				{
					type: window.top.location.search,
					source: "__processMutationTarget",
					error: { stack: e.stack, message: e.message, name: e.name },
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				});
		}
	};

	window.__processMutationRecord = function (record) {
		try {
			let mRecord = {};
			mRecord["addedNodes"] = window.__processNodeList(record.addedNodes);
			mRecord["attributeName"] = record.attributeName;
			mRecord["attributeNamespace"] = record.attributeNamespace;
			mRecord["nextSibling"] =
				record.nextSibling != null
					? window.__extractNodeInfo(record.nextSibling, true)
					: null;
			mRecord["previousSibling"] =
				record.previousSibling != null
					? window.__extractNodeInfo(record.previousSibling, true)
					: null;
			mRecord["oldValue"] = record.oldValue;
			mRecord["removedNodes"] = window.__processNodeList(
				record.removedNodes
			);
			mRecord["target"] = window.__processMutationTarget(
				record.target,
				record.type
			);
			mRecord["type"] = record.type;
			if (
				mRecord["addedNodes"]?.length > 0 ||
				mRecord["removedNodes"]?.length > 0
			)
				return mRecord;
		} catch (e) {
			window.__dispatchErrorLog(
				{
					type: window.top.location.search,
					source: "__processMutationRecord",
					error: { stack: e.stack, message: e.message, name: e.name },
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				});
		}
	};

	const __mutationCallback = (mutationsList, observer) => {
		try {
			for (let mutation of mutationsList) {
				let mRecord = __processMutationRecord(mutation);
				if (mRecord) window.__dispatchMutationData(mRecord);
			}
		} catch (e) {
			window.__dispatchErrorLog(
				{
					type: window.top.location.search,
					source: "__mutationCallback",
					error: { stack: e.stack, message: e.message, name: e.name },
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				});
		}
	};

	const __observer = new MutationObserver(__mutationCallback);

	__observer.observe(document, {
		attributes: true,
		attributeOldValue: true,
		childList: true,
		subtree: true,
	});
})();