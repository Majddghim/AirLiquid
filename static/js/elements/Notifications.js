var GetBrightness = (hex) => {
    var hex = hex.substring(1);
    var rgb = parseInt(hex, 16);
    var r = (rgb >> 16) & 0xff;
    var g = (rgb >> 8) & 0xff;
    var b = (rgb >> 0) & 0xff;
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

class Notifications {

    static Colors = {
        white: "#fffffc",
        black: "#323232",
        green: "#38b48b",
        blue: "#2ca9e1",
        red: "#e9546b",
        orange: "#f89406",
    }

    prefix = "magmanotifications-";

    constructor(options = {}) {
        if (!options.position) options.position = "top-right";
        if (!options.inAnimation) options.inAnimation = "slide";
        if (!options.outAnimation) options.outAnimation = "fade";
        this.inAnimation = options.inAnimation;
        this.outAnimation = options.outAnimation;
        let position = options.position
        this.body = document.querySelector("body");
        this.holder = document.createElement(`div`);
        let marginX = "12px";
        let marginY = "12px";
        let positioning = `right: ${marginX}; top: ${marginY};`;
        if (position == "top-left") positioning = `top: ${marginY};`;
        else if (position == "bottom-left") positioning = `bottom: ${marginY};`;
        else if (position == "bottom-right") positioning = `bottom: ${marginY}; right: ${marginX};`;
        this.holder.style.cssText = `
            position: fixed;
            display: flex;
            gap: 8px;
            flex-direction: column-reverse;
            ${positioning}
            min-width: 200px;
            max-width: 300px;
            z-index: 999;
        `;
        this.body.appendChild(this.holder);
        this.template = document.createElement(`div`);
        this.template.style.cssText = `
            position: relative;
            left: 110%;
            opacity: 0;
            display: flex;
            gap: 8px;
            border-radius: 6px;
            padding: 4px 8px;
            box-shadow: 0 0 10px #00000063;
            border: 2px solid #ffffff29;
            align-items: center;
            transition: .2s;
        `;
        this.template.innerHTML = `
            <div class="${this.prefix}icon">
                <i class="fa-solid fa-circle-exclamation"></i>
            </div>
            <div class="${this.prefix}info">
                <div class="${this.prefix}head">
                    <div class="${this.prefix}title">
                    </div>
                    <div class="${this.prefix}remove">
                    ✕
                    </div>
                </div>
                <div class="${this.prefix}message">
                </div>
            </div>
        `;
        let {info, head, icon, title, message, remove} = this.ExtractNotification(this.template);
        icon.style.cssText = `
            font-size: 32px;
        `;
        // title.style.fontWeight = "bold";
        title.style.cssText = `
            font-size: 16px;
            word-break: break-word;
        `;
        message.style.cssText = `
            font-size: 16px;
            word-break: break-word;
            line-height: 1.3;
        `;
        info.style.cssText = `
            display: flex;
            width: 100%;
            flex-direction: column;
        `;
        head.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        `;
        remove.style.cssText = `
            cursor: pointer;
        `;

        let _this = this;
        /*window.onload = function() {
            _this.IconsCheck(_this);
        }*/
    }

    IconsCheck(self) {
        if (!self) self = this;
        var i = document.createElement('i');
        i.className = 'fa-solid fa fas';
        i.style.display = 'none';
        document.body.insertBefore(i, document.body.firstChild);
        self.icons = window.getComputedStyle(i, null).getPropertyValue("font-family").includes("Font Awesome");
        document.body.removeChild(i);
    }

    querySelector(where, query) {
        return where.querySelector(`.${this.prefix}${query}`);
    }

    ExtractNotification(notification) {
        return {
            title: notification.querySelector(`.${this.prefix}title`),
            message: notification.querySelector(`.${this.prefix}message`),
            icon: notification.querySelector(`.${this.prefix}icon`),
            remove: notification.querySelector(`.${this.prefix}remove`),
            info: notification.querySelector(`.${this.prefix}info`),
            head: notification.querySelector(`.${this.prefix}head`),
        }
    }

    #CreateNotification(ntitle = "", nmessage = "", ncolor, ntime) {
        if (!ntime) ntime = 3500;
        if (!ncolor) ncolor = Notifications.Colors.white;
        nmessage = nmessage.trim();
        ntitle = ntitle.trim();
        let root = this.template.cloneNode(true);
        let {title, message, icon, remove} = this.ExtractNotification(root);
        let _this = this;
        remove.addEventListener("click", function (e) {
            let t = Number(root.style.transitionDuration.replace("s", "")) * 1000;
            if (_this.outAnimation == "fade") {
                root.style.opacity = 0;
            } else if (_this.outAnimation == "slide") {
                root.style.left = "110%";
            }
            root.style.height = window.getComputedStyle(root).height;
            root.style.overflow = "hidden";

            setTimeout(() => {
                root.style.height = "0px";
                root.style.padding = "0px";
                setTimeout(() => {
                    root.remove();
                }, t);
            }, t);
        });
        ncolor = Notifications.Colors[ncolor] ? Notifications.Colors[ncolor] : ncolor;
        root.style.backgroundColor = ncolor;
        if (GetBrightness(ncolor) <= 162) root.style.color = "white";
        title.innerText = ntitle;
        message.innerText = nmessage;
        if (ntitle?.trim() == "" || !ntitle) {
            message.remove();
            title.innerText = nmessage;
            title.style.lineHeight = "1.3";
        }
        if (!this.icons) {
            icon.style.display = "none";
        }
        this.holder.append(root);

        setTimeout(() => {
            if (_this.inAnimation == "fade") root.style.opacity = 1;
            else if (_this.inAnimation == "slide") {
                root.style.opacity = 1;
                root.style.left = "0px";
            }
        }, 100);
        if (ntime != -1) {
            setTimeout(() => {
                remove.click();
            }, ntime);
        }
        return {root, title, message, icon};
    }


    //User Methods

    Notify(title = "", message = "", color, time) {
        let notif = this.#CreateNotification(title, message, color, time);
    }

    Success(title = "", message = "", time) {
        let notif = this.#CreateNotification(title, message, Notifications.Colors.green, time);
        notif.icon.innerHTML = `<i class="fa-solid fa-check"></i>`;
    }

    Error(title = "", message = "", time) {
        let notif = this.#CreateNotification(title, message, Notifications.Colors.red, time);
        notif.icon.innerHTML = `<i class="fa-solid fa-circle-xmark"></i>`;
    }

    Warning(title = "", message = "", time) {
        let notif = this.#CreateNotification(title, message, Notifications.Colors.orange, time);
        notif.icon.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i>`;
    }

    Info(title = "", message = "", time) {
        let notif = this.#CreateNotification(title, message, Notifications.Colors.blue, time);
        notif.icon.innerHTML = `<i class="fa-solid fa-comments"></i>`;
    }

    success = this.Success;
    error = this.Error;
    warning = this.Warning;
    warn = this.Warning;
    info = this.Info;
}