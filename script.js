// Initialize the map
var map = L.map('map').setView([20.5937, 78.9629], 5); // Centered on India

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Function to fetch AQI data from API
async function fetchAQIData(city) {
    try {
        const response = await fetch(`https://api.waqi.info/feed/${city}/?token=57e6ed6a3de4698bc8666439ed6a076c84bcab31`);
        const data = await response.json();

        if (data.status === "ok") {
            const aqi = data.data.aqi;
            const pollutants = data.data.iaqi;
            updateAQIInfo(aqi, pollutants);
        } else {
            alert("City not found or API limit exceeded.");
        }
    } catch (error) {
        console.error("Error fetching AQI data:", error);
    }
}

// Function to update AQI information panel
function updateAQIInfo(aqi, pollutants) {
    document.getElementById("aqiValue").innerHTML = `AQI: ${aqi}`;
    document.getElementById("qualityStatus").innerHTML = `Air Quality: ${getAirQualityStatus(aqi)}`;

    document.getElementById("co").innerHTML = `CO: ${pollutants.co?.v || "--"}%`;
    document.getElementById("no").innerHTML = `NO: ${pollutants.no?.v || "--"}%`;
    document.getElementById("no2").innerHTML = `NO2: ${pollutants.no2?.v || "--"}%`;
    document.getElementById("o3").innerHTML = `O3: ${pollutants.o3?.v || "--"}%`;
    document.getElementById("so2").innerHTML = `SO2: ${pollutants.so2?.v || "--"}%`;
    document.getElementById("pm25").innerHTML = `PM2.5: ${pollutants.pm25?.v || "--"}%`;
    document.getElementById("pm10").innerHTML = `PM10: ${pollutants.pm10?.v || "--"}%`;
    document.getElementById("nh3").innerHTML = `NH3: ${pollutants.nh3?.v || "--"}%`;
}

// Function to determine air quality status based on AQI value
function getAirQualityStatus(aqi) {
    if (aqi <= 50) return "Good";
    if (aqi <= 100) return "Moderate";
    if (aqi <= 150) return "Unhealthy for Sensitive Groups";
    if (aqi <= 200) return "Unhealthy";
    if (aqi <= 300) return "Very Unhealthy";
    return "Hazardous";
}

// Add event listener to button
document.getElementById("fetchDataBtn").addEventListener("click", () => {
    const city = document.getElementById("cityInput").value.trim();
    if (city) {
        fetchAQIData(city);
    } else {
        alert("Please enter a city name.");
    }
});
