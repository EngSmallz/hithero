(function () {
    function setButtonVisible(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button) {
            return;
        }
        button.classList.remove("hidden");
        button.classList.add("block");
    }

    window.redirectTo = function redirectTo(url) {
        window.location.href = url;
    };

    window.toggleMenu = function toggleMenu() {
        const menuItems = document.getElementById("menuItems");
        if (!menuItems) {
            return;
        }

        menuItems.classList.toggle("hidden");
        if (!menuItems.classList.contains("hidden")) {
            window.checkAuthentication();
        }
    };

    window.checkAuthentication = async function checkAuthentication() {
        const buttons = ["loginButton", "logoutButton", "mypageButton", "validationButton", "forumButton"];
        buttons.forEach((id) => {
            const button = document.getElementById(id);
            if (button) {
                button.classList.add("hidden");
                button.classList.remove("block");
            }
        });

        let userRole = null;
        try {
            const response = await fetch("/api/profile/");
            if (response.ok) {
                const data = await response.json();
                if (data && data.user_role) {
                    userRole = data.user_role;
                }
            }
        } catch (error) {
            console.error("Error fetching user profile:", error);
        }

        if (userRole === "teacher") {
            setButtonVisible("logoutButton");
            setButtonVisible("mypageButton");
            setButtonVisible("forumButton");
            setButtonVisible("validationButton");
            return;
        }

        if (userRole === "admin") {
            setButtonVisible("logoutButton");
            setButtonVisible("forumButton");
            setButtonVisible("validationButton");
            return;
        }

        setButtonVisible("loginButton");
    };

    window.logout = async function logout() {
        try {
            const response = await fetch("/profile/logout/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (response.ok) {
                window.location.href = "/";
            } else {
                console.error("Logout failed:", response.status);
                alert("Logout failed. Please try again.");
            }
        } catch (error) {
            console.error("Error during logout:", error);
            alert("An error occurred during logout. Please try again.");
        }
    };

    window.mypage = async function mypage() {
        try {
            const response = await fetch("/profile/myinfo/", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (response.ok) {
                window.location.href = "/pages/teacher.html";
            } else {
                console.error("Error fetching my page info:", response.status);
                window.location.href = "/";
            }
        } catch (error) {
            console.error("Error fetching my page info:", error);
            window.location.href = "/";
        }
    };
})();
