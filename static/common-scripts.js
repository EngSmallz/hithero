// ====================================================================
// HOMEROOM HEROES - COMMON JAVASCRIPT LOGIC
// ====================================================================


// --- I. CORE UTILITY & NAVIGATION FUNCTIONS (Global Scope) ---
// These functions are attached to HTML elements (e.g., onclick="redirectTo(...)") 
// so they must be in the global scope.

/**
 * Redirects the user to a specified URL.
 * @param {string} url - The URL to redirect to.
 */
function redirectTo(url) {
    window.location.href = url;
}

/**
 * Toggles the visibility of the mobile navigation menu.
 */
function toggleMenu() {
    const menuItems = document.getElementById('menuItems');
    // Using optional chaining (?) and classList.toggle for clean Tailwind management
    menuItems?.classList.toggle('hidden'); 
}

/**
 * Handles the user logout process via an API call.
 */
async function logout() {
    try {
        const response = await fetch(`/profile/logout/`, { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) { 
            window.location.href = '/'; 
        } else { 
            console.error('Logout failed:', response.status); 
            alert('Logout failed. Please try refreshing.'); 
        }
    } catch (error) { 
        console.error('Error during logout:', error); 
        alert('A network error occurred during logout.'); 
    }
}

/**
 * Redirects an authenticated user (like a teacher) to their dedicated page.
 */
async function mypage() {
    try {
        const response = await fetch('/profile/myinfo/', { 
            method: 'GET', 
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) { 
            window.location.href = '/pages/teacher.html'; 
        } else { 
            console.error('Error fetching my page info:', response.status); 
            window.location.href = '/'; // Redirect to home/login if error
        }
    } catch (error) { 
        console.error('Error fetching my page info:', error); 
        window.location.href = '/'; // Redirect on network error
    }
}


// --- II. UNIVERSAL MODAL CONTROLS (T&C and Wishlist) ---
// Functions for opening and closing common modal windows.

/**
 * Opens the Terms and Conditions modal.
 */
function openTermsConditions() {
    document.getElementById('termsConditionsModal')?.classList.remove('hidden');
}

/**
 * Closes the Terms and Conditions modal.
 */
function closeTermsConditions() {
    document.getElementById('termsConditionsModal')?.classList.add('hidden');
}

/**
 * Opens the Wishlist Setup modal.
 */
function openWishlistSetup() {
    document.getElementById('wishlistModal').style.display = 'flex';
}

/**
 * Closes the Wishlist Setup modal.
 */
function closeWishlistSetup() {
    document.getElementById('wishlistModal').style.display = 'none';
}


// --- III. DYNAMIC DROPDOWN API HANDLERS (Location/School) ---
// Functions responsible for fetching and populating location-based dropdowns.

async function populateStatesDropdown() {
    try {
        const response = await fetch("/api/get_states/");
        const states = await response.json();
        const stateDropdown = document.getElementById("state");
        stateDropdown.innerHTML = '<option value="" disabled selected>Choose state</option>';
        states.forEach(state => {
            stateDropdown.add(new Option(state, state));
        });
    } catch (error) {
        console.error("Error retrieving state information:", error);
        alert("Error retrieving state information. " + error.message);
    }
}

async function populateCountiesDropdown() {
    try {
        const selectedState = document.getElementById("state").value;
        const countyDropdown = document.getElementById("county");
        countyDropdown.innerHTML = '<option value="" disabled selected>Choose county</option>';
        if (selectedState) {
            const response = await fetch(`/api/get_counties/${selectedState}`);
            const counties = await response.json();
            counties.forEach(county => {
                countyDropdown.add(new Option(county, county));
            });
        }
        document.getElementById("district").innerHTML = '<option value="" disabled selected>Choose district</option>';
        document.getElementById("school").innerHTML = '<option value="" disabled selected>Choose school</option>';
    } catch (error) {
        console.error("Error retrieving county information:", error);
        alert("Error retrieving county information. " + error.message);
    }
}

async function populateDistrictsDropdown() {
    try {
        const selectedState = document.getElementById("state").value;
        const selectedCounty = document.getElementById("county").value;
        const districtDropdown = document.getElementById("district");
        districtDropdown.innerHTML = '<option value="" disabled selected>Choose district</option>';
        if (selectedState && selectedCounty) {
            const response = await fetch(`/api/get_districts/${selectedState}/${selectedCounty}`);
            const districts = await response.json();
            districts.forEach(district => {
                districtDropdown.add(new Option(district, district));
            });
        }
        document.getElementById("school").innerHTML = '<option value="" disabled selected>Choose school</option>';
    } catch (error) {
        console.error("Error retrieving district information:", error);
        alert("Error retrieving district information. " + error.message);
    }
}

async function populateSchoolsDropdown() {
    try {
        const selectedState = document.getElementById("state").value;
        const selectedCounty = document.getElementById("county").value;
        const selectedDistrict = document.getElementById("district").value;
        const schoolDropdown = document.getElementById("school");
        schoolDropdown.innerHTML = '<option value="" disabled selected>Choose school</option>';
        if (selectedState && selectedCounty && selectedDistrict) {
            const response = await fetch(`/api/get_schools/${selectedState}/${selectedCounty}/${selectedDistrict}`);
            const schools = await response.json();
            schools.forEach(school => {
                schoolDropdown.add(new Option(school, school));
            });
        }
    } catch (error) {
        console.error("Error retrieving school information:", error);
        alert("Error retrieving school information. " + error.message);
    }
}


// --- IV. FORM UTILITY FUNCTIONS (e.g., Character Count) ---
// Utility functions for form input fields.

/**
 * Updates the character count display for the 'aboutMe' textarea.
 */
function updateCharacterCount() {
    const maxLength = 500;
    const currentLength = document.getElementById("aboutMe").value.length;
    const charsRemaining = maxLength - currentLength;
    const countElement = document.getElementById("charCount");
    countElement.textContent = charsRemaining + " characters remaining";
}
