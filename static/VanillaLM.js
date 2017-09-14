VanillaLM = {
    timeoutInSeconds: 5,
    state: {},
    openRequests: {},
    defaultConfigs: {},
    configs: {},
    storage: { //a fake storage to be overwritten by sessionStorage
        _data: {},
        setItem: function (id, val) {
            return this._data[id] = String(val);
        },
        getItem: function (id) {
            return this._data.hasOwnProperty(id) ? this._data[id] : undefined;
        },
        removeItem: function (id) {
            return delete this._data[id];
        },
        clear: function () {
            return this._data = {};
        }
    },
    /**
     * Returns the value of the given attribute. This attribute may be set immediatly before or on another page
     * during the same session.
     * @param parameter: name of the attribute
     * @returns {*}
     */
    getAttribute: function (parameter) {
        if (typeof VanillaLM.state.properties[parameter] !== "undefined") {
            return VanillaLM.state.properties[parameter];
        } else {
            var session = JSON.parse(window.sessionStorage.getItem("VanillaLM.sessionStorage"));
            return session.properties[parameter];
        }
    },
    /**
     * Sets an attribute for the user. For example an attribute could be "current page".
     * @param string parameter: name of the attribute
     * @param value: value of the attribute
     */
    setAttribute: function (parameter, value) {
        if (typeof VanillaLM.state.properties === "undefined") {
            VanillaLM.state.properties = {};
        }
        VanillaLM.state.properties[parameter] = value;
    },
    setDefaultConfigs: function (parameter) {
        VanillaLM.defaultConfigs = parameter;
        for (var i in parameter) {
            if (typeof VanillaLM.configs[i] === "undefined") {
                VanillaLM.configs[i] = parameter[i];
            }
        }
        var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage") || "{}");
        VanillaLM.state = Object.assign(session, VanillaLM.state);
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
        var promise = new Promise(function (resolve, reject) {
            var opener = window.opener || window.parent;
            var request_id = Math.floor(Math.random() * 1000000);
            opener.postMessage(JSON.stringify({
                "secret": VanillaLM.state.secret,
                "request": "/configs",
                request_id: request_id,
                "default_configs": VanillaLM.defaultConfigs
            }), "*");
            VanillaLM.openRequests[request_id] = {
                "resolve": resolve,
                "reject": reject,
                "callable": function (output) {
                    for (var i in output.configs) {
                        VanillaLM.configs[i] = output.configs[i];
                    }
                },
                "time": new Date()
            };
            //Now the request is sent to the LMS and we wait for a response ...
        })
        return promise;
    },
    getConfig: function (parameter) {
        return VanillaLM.configs[parameter];
    },
    /**
     * Marks the module as successfully finished. Don't forget to trigger the method send as well.
     */
    markSuccess: function () {
        VanillaLM.state.success = 1;
    },
    /**
     * This adds points to the score of the user. If this user already has some points of the pointclass (type)
     * then they will be added )or subtracted if number is negative).
     * @param string pointclass: name of the type of points like
     * @param number
     */
    addPoints: function (pointclass, number) {
        if (typeof VanillaLM.state.points === "undefined") {
            VanillaLM.state.points = {};
        }
        VanillaLM.state.points[pointclass] = VanillaLM.getPoints(pointclass) + number;
    },
    setPoints: function (pointclass, number) {
        if (typeof VanillaLM.state.points === "undefined") {
            VanillaLM.state.points = {};
        }
        VanillaLM.state.points[pointclass] = number;
    },
    /**
     * Gets the amount of points of pointclass the user already has received (combined in this session).
     * @param string pointclass: the type of points.
     * @returns integer|float
     */
    getPoints: function (pointclass) {
        if (typeof VanillaLM.state.points[pointclass] !== "undefined") {
            return VanillaLM.state.points[pointclass];
        } else {
            var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage"));
            if ((typeof session.points !== "undefined") && (typeof session.points[pointclass] !== "undefined")) {
                return session.points[pointclass];
            } else {
                return 0;
            }
        }
    },
    /**
     * Sends the current state to the opener-window and saves the new state to the sessionStorage (if available).
     */
    send: function () {
        var opener = window.opener || window.parent;
        var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage") || "{}");
        VanillaLM.state = Object.assign(session, VanillaLM.state);
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
        if (opener) {
            opener.postMessage(JSON.stringify(VanillaLM.state), "*");
        }
    },
    /**
     * Returns a promise for delivering actor-information. You can write VanillaLM.getActor().then(function(actor) { ... });
     * or you could write it with a callback VanillaLM.getActor(function (actor) { if (actor} { .... } );
     * Note that the callback is called even if the request was timed out. Then the actor variable will be false.
     * @param callable : Will be called after the response arrives or if the request is timed out. It will get
     *                   the actor-information on success or a simple false if their is no information about the actor available.
     */
    getActor: function (callable) {
        var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage") || "{}");
        VanillaLM.state = Object.assign(session, VanillaLM.state);
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
        return new Promise(function (resolve, reject) {
            var opener = window.opener || window.parent;
            var request_id = Math.floor(Math.random() * 1000000);
            opener.postMessage(JSON.stringify({
                secret: VanillaLM.state.secret,
                request: "/actor/current",
                request_id: request_id
            }), "*");
            VanillaLM.openRequests[request_id] = {
                "resolve": resolve,
                "reject": reject,
                "callable": callable,
                "time": new Date()
            };
            //Now the request is sent to the LMS and we wait for a response ...
        });
    },
    getStyle: function (callable) {
        var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage") || "{}");
        VanillaLM.state = Object.assign(session, VanillaLM.state);
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
        return new Promise(function (resolve, reject) {
            var opener = window.opener || window.parent;
            var request_id = Math.floor(Math.random() * 1000000);
            opener.postMessage(JSON.stringify({
                secret: VanillaLM.state.secret,
                request: "/style",
                request_id: request_id
            }), "*");
            VanillaLM.openRequests[request_id] = {
                "resolve": resolve,
                "reject": reject,
                "callable": callable,
                "time": new Date()
            };
            //Now the request is sent to the LMS and we wait for a response ...
        });
    },
    invite: function (max, parameter, callable) {
        var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage") || "{}");
        VanillaLM.state = Object.assign(session, VanillaLM.state);
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
        return new Promise(function (resolve, reject) {
            var opener = window.opener || window.parent;
            var request_id = Math.floor(Math.random() * 1000000);
            opener.postMessage(JSON.stringify({
                "secret": VanillaLM.state.secret,
                "request": "/invite",
                "request_id": request_id,
                "max": max,
                "parameter": parameter
            }), "*");
            VanillaLM.openRequests[request_id] = {
                "resolve": resolve,
                "reject": reject,
                "callable": callable,
                "time": new Date()
            };
            //Now the request is sent to the LMS and we wait for a response ...
        });
    },
    terminateInvitation: function (vanillalm_game_id, callable) {
        var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage") || "{}");
        VanillaLM.state = Object.assign(session, VanillaLM.state);
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
        return new Promise(function (resolve, reject) {
            var opener = window.opener || window.parent;
            var request_id = Math.floor(Math.random() * 1000000);
            opener.postMessage(JSON.stringify({
                "secret": VanillaLM.state.secret,
                "request": "/terminateInvitation",
                "request_id": request_id,
                "vanillalm_game_id": vanillalm_game_id
            }), "*");
            VanillaLM.openRequests[request_id] = {
                "resolve": resolve,
                "reject": reject,
                "callable": callable,
                "time": new Date()
            };
            //Now the request is sent to the LMS and we wait for a response ...
        });
    },
    postTimelineMessage: function (message) {
        var opener = window.opener || window.parent;
        opener.postMessage(JSON.stringify({
            "secret": VanillaLM.state.secret,
            "request": "/postTimelineMessage",
            "message": message
        }), "*");
    },
    /**
     * Sets a property if the current state. Note that this can erase all points, mark the module as successful
     * or erase all attributes by accident. Use method setAttribute or addPoints instead if possible.
     * @param paramater
     * @param value
     */
    set: function (paramater, value) {
        VanillaLM.state[parameter] = value;
    },
    get: function (paramater, value) {
        if (typeof VanillaLM.state[parameter] !== "undefined") {
            return VanillaLM.state[parameter];
        } else {
            var session = JSON.parse(VanillaLM.storage.getItem("VanillaLM.sessionStorage"));
            return session[parameter];
        }
    },
    /**
     * Returns a GET parameter of the current request. Only used to extract the secret-parameter.
     * @param parameterName
     * @returns string: value of GET parameter
     */
    findGetParameter: function(parameterName) {
        var result = null,
            tmp = [];
        location.search
            .substr(1)
            .split("&")
            .forEach(function (item) {
                tmp = item.split("=");
                if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
            });
        return result;
    }
};

/**
 * Now some startup procedure: If this page has a secret in its URL, we need to save that.
 */
document.addEventListener("DOMContentLoaded", function(event) {
    setInterval(function () { //cleanup method for open request which are timed out
        for (var request_id in VanillaLM.openRequests) {
            if (new Date() - VanillaLM.openRequests[request_id].time > 1000 * VanillaLM.timeoutInSeconds) { //after 5 seconds
                VanillaLM.openRequests[request_id].reject();
                if (typeof VanillaLM.openRequests[request_id].callable === "function") {
                    VanillaLM.openRequests[request_id].callable(false);
                }
                delete VanillaLM.openRequests[request_id];
            }
        }
    }, 500);
    window.addEventListener("message", function (event) {
        var message = JSON.parse(event.data);
        if (message.secret === VanillaLM.state.secret && typeof VanillaLM.openRequests[message.request_id] !== "undefined") {
            var request_id = message.request_id;
            delete message.request_id;
            delete message.secret;
            VanillaLM.openRequests[request_id].resolve(message);
            if (typeof VanillaLM.openRequests[request_id].callable === "function") {
                VanillaLM.openRequests[request_id].callable(message);
            }
            delete VanillaLM.openRequests[request_id];
        }

    }, false);

    //save secret in sessionStorage
    var secret = VanillaLM.findGetParameter("vanillalm_secret");
    try {
        window.sessionStorage;
        if (typeof window.sessionStorage !== "undefined") {
            VanillaLM.storage = window.sessionStorage;
        }
    } catch(exception) {}
    if (secret) {
        VanillaLM.state.secret = secret;
        VanillaLM.storage.setItem("VanillaLM.sessionStorage", JSON.stringify(VanillaLM.state));
    }

    VanillaLM.getStyle().then(function (style) {
        //set styles to CSS custom attributes (CSS variables):
        var root = document.querySelector(':root');
        root.style.setProperty("--vanillalm-color", style["color"]);
        root.style.setProperty("--vanillalm-background-color", style["background-color"]);
        root.style.setProperty("--vanillalm-font-family", style["font-family"]);
        root.style.setProperty("--vanillalm-link-color", style["color_a"]);
        //root.style.setProperty("--vanillalm-link-color-hover", style["color_a_hover"]); //adly it's not possible to retrieve the hover-color with JS.
    });
});
