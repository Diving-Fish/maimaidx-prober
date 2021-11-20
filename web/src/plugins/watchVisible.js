export default function watchVisible(property, title, that) {
    return function (visible) {
        if (!that) that = this;
        let state;
        function popstateListener() {
            if (window.history.state == state ||
                (window.history.state && state && window.history.state.title === state.title)) {
                that[property] = false;
                window.removeEventListener("popstate", popstateListener);
            }
        }
        if (visible) {
            state = window.history.state;
            window.history.pushState(
                { title: title, url: `#${title}` },
                title,
                `#${title}`
            );
            window.addEventListener("popstate", popstateListener);
        } else {
            if (window.history.state && window.history.state.title === title)
                window.history.back();
        }
    };
}
