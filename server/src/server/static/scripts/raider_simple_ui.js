(() => {
	window.onload = function () {
		let pollCounter = 0;
		async function __run() {
			if (pollCounter++ < 10) {
				await __pollStorage();
				setTimeout(__run, 500);
			}
		}
		__run();
	};

	window.addEventListener("beforeunload", async function (e) {
		let localStorageData = {};
		let sessionStorageData = {};

		if (indexedDB.databases && chrome !== undefined) {
			let totalDBData = await window.getIndexedDBData()
				.then((result) => {
					return result;
				})
				.then((totalDBData) => {
					setTimeout(async () => {
						if (
							totalDBData?.dataValues !== undefined &&
							totalDBData?.dbName !== undefined
						)
							navigator.sendBeacon(
								`${window.location.origin}${window.location.pathname}poll`,
								JSON.stringify(
									{
										type: "idb",
										data: totalDBData,
										stage: "beforeunload",
										url: window.location.href,
										contextURL: document.location.href,
										extensionId: new URLSearchParams(
											window.location.search
										).get("extensionId"),
										visit: new URLSearchParams(window.location.search).get(
											"visit"
										),
									},
									window.__getCircularReplacer()
								)
							);
					}, 2000);
				});
		}
		for (let key of Object.getOwnPropertyNames(window.localStorage)) {
			localStorageData[key] = window.localStorage[key];
		}
		for (let key of Object.getOwnPropertyNames(window.sessionStorage)) {
			sessionStorageData[key] = window.sessionStorage[key];
		}
		if (Object.keys(localStorageData).length) {
			let data = JSON.stringify(
				{
					type: "local",
					data: localStorageData,
					stage: "beforeunload",
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer()
			);
			navigator.sendBeacon(
				`${window.location.origin}${window.location.pathname}poll`,
				data
			);
		}

		if (Object.keys(sessionStorageData).length) {
			let data = JSON.stringify(
				{
					type: "session",
					data: sessionStorageData,
					stage: "beforeunload",
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer()
			);
			navigator.sendBeacon(
				`${window.location.origin}${window.location.pathname}poll`,
				data
			);
		}

		if (window.__cookieGetter() !== "") {
			let data = JSON.stringify(
				{
					type: "cookies",
					data: window.__cookieGetter(),
					stage: "beforeunload",
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer()
			);
			navigator.sendBeacon(
				`${window.location.origin}${window.location.pathname}poll`,
				data
			);
		}
		let variables = {};
		for (let prop of Object.getOwnPropertyNames(window)) {
			if (seenVars.has(prop)) continue;
			variables[prop] = window[prop];
		}
		for (let prop of Object.getOwnPropertyNames(document)) {
			if (prop === 'location') continue;
			variables[prop] = document[prop];
		}
		if (Object.keys(variables).length > 0) {
			for (let key of Object.keys(variables)) {
				try {
					JSON.stringify(
						variables[key],
						window.__getCircularReplacer()
					);
				} catch (e) {
					delete variables[key];
				}
			}
			let data = JSON.stringify(
				{
					variables,
					type: "variable",
					stage: "beforeunload",
					url: window.location.href,
					contextURL: document.location.href,
					extensionId: new URLSearchParams(window.location.search).get(
						"extensionId"
					),
					visit: new URLSearchParams(window.location.search).get("visit"),
				},
				window.__getCircularReplacer()
			);
			navigator.sendBeacon(
				`${window.location.origin}${window.location.pathname}poll`,
				data
			);
		}
	});
})();