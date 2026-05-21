(function () {
    const defaultConfig = {
        stateUrl: "/api/get_states/",
        countiesUrl: function (state) {
            return "/api/get_counties/" + state;
        },
        districtsUrl: function (state, county) {
            return "/api/get_districts/" + state + "/" + county;
        },
        schoolsUrl: function (state, county, district) {
            return "/api/get_schools/" + state + "/" + county + "/" + district;
        },
        stateError: "Error retrieving state information. Please try again later.",
        countyError: "Error retrieving county information. Please try again later.",
        districtError: "Error retrieving district information. Please try again later.",
        schoolError: "Error retrieving school information. Please try again later.",
    };

    let activeConfig = Object.assign({}, defaultConfig);

    function setSelectToPrompt(selectId, label) {
        const select = document.getElementById(selectId);
        if (!select) {
            return null;
        }
        select.innerHTML = "";
        const promptOption = new Option(label, "", true, true);
        promptOption.disabled = true;
        select.add(promptOption);
        return select;
    }

    async function fetchJson(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Network response was not ok.");
        }
        return response.json();
    }

    window.configureSchoolDropdowns = function configureSchoolDropdowns(config) {
        activeConfig = Object.assign({}, defaultConfig, config || {});
    };

    window.populateStatesDropdown = async function populateStatesDropdown() {
        try {
            const states = await fetchJson(activeConfig.stateUrl);
            const stateDropdown = setSelectToPrompt("state", "Choose state");
            if (!stateDropdown) {
                return;
            }
            states.forEach(function (state) {
                stateDropdown.add(new Option(state, state));
            });
        } catch (error) {
            console.error("Error retrieving state information:", error);
            alert(activeConfig.stateError);
        }
    };

    window.populateCountiesDropdown = async function populateCountiesDropdown() {
        const selectedState = (document.getElementById("state") || {}).value;
        setSelectToPrompt("county", "Choose county");
        setSelectToPrompt("district", "Choose district");
        setSelectToPrompt("school", "Choose school");

        if (!selectedState) {
            return;
        }

        try {
            const counties = await fetchJson(activeConfig.countiesUrl(selectedState));
            const countyDropdown = document.getElementById("county");
            if (!countyDropdown) {
                return;
            }
            counties.forEach(function (county) {
                countyDropdown.add(new Option(county, county));
            });
        } catch (error) {
            console.error("Error retrieving county information:", error);
            alert(activeConfig.countyError);
        }
    };

    window.populateDistrictsDropdown = async function populateDistrictsDropdown() {
        const selectedState = (document.getElementById("state") || {}).value;
        const selectedCounty = (document.getElementById("county") || {}).value;
        setSelectToPrompt("district", "Choose district");
        setSelectToPrompt("school", "Choose school");

        if (!selectedState || !selectedCounty) {
            return;
        }

        try {
            const districts = await fetchJson(activeConfig.districtsUrl(selectedState, selectedCounty));
            const districtDropdown = document.getElementById("district");
            if (!districtDropdown) {
                return;
            }
            districts.forEach(function (district) {
                districtDropdown.add(new Option(district, district));
            });
        } catch (error) {
            console.error("Error retrieving district information:", error);
            alert(activeConfig.districtError);
        }
    };

    window.populateSchoolsDropdown = async function populateSchoolsDropdown() {
        const selectedState = (document.getElementById("state") || {}).value;
        const selectedCounty = (document.getElementById("county") || {}).value;
        const selectedDistrict = (document.getElementById("district") || {}).value;
        setSelectToPrompt("school", "Choose school");

        if (!selectedState || !selectedCounty || !selectedDistrict) {
            return;
        }

        try {
            const schools = await fetchJson(activeConfig.schoolsUrl(selectedState, selectedCounty, selectedDistrict));
            const schoolDropdown = document.getElementById("school");
            if (!schoolDropdown) {
                return;
            }
            schools.forEach(function (school) {
                schoolDropdown.add(new Option(school, school));
            });
        } catch (error) {
            console.error("Error retrieving school information:", error);
            alert(activeConfig.schoolError);
        }
    };
})();
