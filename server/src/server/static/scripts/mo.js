(() => {
	const __dispatchMutationData = function (data) {
		let parsed_data;
		try {
			parsed_data = JSON.__stringify.__apply(this, [
				{
					type: "mutation",
					data,
					extensionId: new URLSearchParams(window.location.search).__get(
						"extensionId"
					),
					url: window.location.href,
					contextURL: document.location.href,
					visit: new URLSearchParams(window.location.search).__get("visit"),
				},
				__getCircularReplacer(),
			]);
			// console.__log(parsed_data);
			__fetch(`${location.origin}${window.location.pathname}mutation`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: parsed_data,
			});
		} catch (e) {
			__dispatchErrorLog({
				type: "mutation.html",
				source: "__dispatchMutationData",
				error: { stack: e.stack, message: e.message, name: e.name },
				url: window.location.href,
				contextURL: document.location.href,
				extensionId: new URLSearchParams(window.location.search).__get(
					"extensionId"
				),
				visit: new URLSearchParams(window.location.search).__get("visit"),
			});
		}
	};

	const __processScriptSrc = function (src) {
		src = src?.__split("?")[0]?.__split("#")[0];
		if (
			!__injectURLs.__has(src) &&
			!src.__startsWith("http://testserver.com:9000/static") &&
			!src.__startsWith("https://testserver.com:9010/static")
		) {
			__injectURLs.__add(src);
			let extensionId = new URLSearchParams(window.location.search).__get(
				"extensionId"
			);
			let timestamp = undefined;
			try {
				timestamp = Date.__now();
			} catch (e) { }
			data = {
				timestamp,
				extensionId,
				type: "dosglobalvars",
				scriptname: src,
			};
			__fetch("/logscriptname", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(data),
			});
		}
	};

	const __extractNodeInfo = function (node, isSibling = false) {
		try {
			let data = {};
			data["name"] = node.nodeName;
			if (
				node.innerText?.__includes("_storageProxy") ||
				node.innerText?.__includes("__hookProperty") ||
				node.innerText?.__includes("function __hook(object, property, tag)")
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
			__dispatchErrorLog({
				type: "mutation.html",
				source: "__extractNodeInfo",
				error: { stack: e.stack, message: e.message, name: e.name },
				url: window.location.href,
				contextURL: document.location.href,
				extensionId: new URLSearchParams(window.location.search).__get(
					"extensionId"
				),
				visit: new URLSearchParams(window.location.search).__get("visit"),
			});
		}
	};

	const __processNodeList = function (nodeList) {
		let nodeListData = [];
		try {
			if (nodeList === undefined || nodeList.length === 0) return undefined;
			try {
				nodeList.__forEach((node) => {
					let nodeData = __extractNodeInfo(node);
					if (!__knownHashes.__has(nodeData.hash)) {
						nodeListData.__push(nodeData);
						__knownHashes.__add(nodeData.hash);
					}
				});
			} catch (e) {
				// console.__error("__processNodeList", e);
			} finally {
				return nodeListData;
			}
		} catch (e) {
			__dispatchErrorLog({
				type: "mutation.html",
				source: "__processNodeList",
				error: { stack: e.stack, message: e.message, name: e.name },
				url: window.location.href,
				contextURL: document.location.href,
				extensionId: new URLSearchParams(window.location.search).__get(
					"extensionId"
				),
				visit: new URLSearchParams(window.location.search).__get("visit"),
			});
		}
	};

	const __processMutationTarget = function (target, type) {
		try {
			let targetData;
			if (type === "childList") {
				targetData = __extractNodeInfo(target);
			} else if (type === "attributes") {
				let attrs = [];
				[...target.attributes].__forEach((a) => {
					attrs.__push(`${a.nodeName}=${a.nodeValue}`);
				});
				targetData = {
					id: target.id,
					attrs,
					classList: Array.__from(target.classList),
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
			__dispatchErrorLog({
				type: "mutation.html",
				source: "__processMutationTarget",
				error: { stack: e.stack, message: e.message, name: e.name },
				url: window.location.href,
				contextURL: document.location.href,
				extensionId: new URLSearchParams(window.location.search).__get(
					"extensionId"
				),
				visit: new URLSearchParams(window.location.search).__get("visit"),
			});
		}
	};

	const __processMutationRecord = function (record) {
		try {
			if (
				record.type === "attributes" &&
				record.attributeName === "src" &&
				record.target.nodeName === "SCRIPT"
			) {
				__processScriptSrc(record.target.src);
			}
			let mRecord = {};
			mRecord["addedNodes"] = __processNodeList(record.addedNodes);
			mRecord["attributeName"] = record.attributeName;
			mRecord["attributeNamespace"] = record.attributeNamespace;
			mRecord["nextSibling"] =
				record.nextSibling != null
					? __extractNodeInfo(record.nextSibling, true)
					: null;
			mRecord["previousSibling"] =
				record.previousSibling != null
					? __extractNodeInfo(record.previousSibling, true)
					: null;
			mRecord["oldValue"] = record.oldValue;
			mRecord["removedNodes"] = __processNodeList(record.removedNodes);
			mRecord["target"] = __processMutationTarget(
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
			__dispatchErrorLog({
				type: "mutation.html",
				source: "__processMutationRecord",
				error: { stack: e.stack, message: e.message, name: e.name },
				url: window.location.href,
				contextURL: document.location.href,
				extensionId: new URLSearchParams(window.location.search).__get(
					"extensionId"
				),
				visit: new URLSearchParams(window.location.search).__get("visit"),
			});
		}
	};

	const __mutationCallback = (mutationsList, observer) => {
		try {
			for (let mutation of mutationsList) {
				let mRecord = __processMutationRecord(mutation);
				if (mRecord) __dispatchMutationData(mRecord);
			}
		} catch (e) {
			__dispatchErrorLog({
				type: window.top.location.search,
				source: "__mutationCallback",
				error: { stack: e.stack, message: e.message, name: e.name },
				url: window.location.href,
				contextURL: document.location.href,
				extensionId: new URLSearchParams(window.location.search).__get(
					"extensionId"
				),
				visit: new URLSearchParams(window.location.search).__get("visit"),
			});
		}
	};

	const __observer = new MutationObserver(__mutationCallback);
	__observer.__observe(document, {
		attributes: true,
		childList: true,
		subtree: true,
	});
})();