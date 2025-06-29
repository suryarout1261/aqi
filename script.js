let map;
let marker;

// Initialize dark mode state from localStorage
const isDarkMode = localStorage.getItem('theme') === 'dark';

function initMap() {
    map = L.map('map').setView([20.5937, 78.9629], 4); // Default center on India
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

function applyDarkMode(isDark) {
    const html = document.documentElement;
    if (isDark) {
        html.setAttribute('data-theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
    }
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function updateTrafficLights(data) {
    // Update timing display
    $('#red-timing').text(data.timings.red + ' sec');
    $('#yellow-timing').text(data.timings.yellow + ' sec');
    $('#green-timing').text(data.timings.green + ' sec');

    // Update traffic data
    $('#traffic-density').text(data.traffic_data.density);
    $('#avg-speed').text(data.traffic_data.speed);
    $('#queue-length').text(data.traffic_data.queue);

    // Update recommendation
    $('#traffic-recommendation').text(data.recommendation);

    // Remove any existing active classes
    $('.light').removeClass('active');

    // Start the traffic light cycle
    startTrafficLightCycle(data.timings);
}

function startTrafficLightCycle(timings) {
    let totalCycle = timings.red + timings.yellow + timings.green;
    let currentTime = Date.now() % totalCycle * 1000;

    // Determine which light should be active
    if (currentTime < timings.red * 1000) {
        $('.light.red').addClass('active');
    } else if (currentTime < (timings.red + timings.yellow) * 1000) {
        $('.light.yellow').addClass('active');
    } else {
        $('.light.green').addClass('active');
    }
}

function updateTrafficData(lat, lon, aqi) {
    $.ajax({
        url: '/traffic-data',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            latitude: lat,
            longitude: lon,
            aqi: aqi
        }),
        success: function(response) {
            updateTrafficLights(response);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching traffic data:', error);
        }
    });
}

$(document).ready(function() {
    // Initialize dark mode
    if (isDarkMode) {
        document.getElementById('theme-switch').checked = true;
        applyDarkMode(true);
    }

    // Theme switch handler
    $('#theme-switch').on('change', function(e) {
        applyDarkMode(e.target.checked);
    });

    // Initialize map
    initMap();

    // Form submission handler
    $('#predictionForm').on('submit', function(e) {
        e.preventDefault();
        
        $.ajax({
            url: '/predict',
            method: 'POST',
            data: {
                city: $('#city').val()
            },
            success: function(response) {
                if (response.error) {
                    alert(response.error);
                    return;
                }
                
                // Update map location
                const lat = response.latitude;
                const lon = response.longitude;
                map.setView([lat, lon], 10);
                
                // Update or add marker
                if (marker) {
                    marker.setLatLng([lat, lon]);
                } else {
                    marker = L.marker([lat, lon]).addTo(map);
                }
                
                // Update AQI value and category
                const aqiValue = response.AQI;
                $('#aqi').text(Math.round(aqiValue));
                $('#aqi-category').text(response.AQI_category);
                
                // Update AQI meter
                const segments = $('.segment');
                segments.removeClass('active');
                
                // Determine active segment based on AQI value
                if (aqiValue <= 50) {
                    $('.segment.good').addClass('active');
                } else if (aqiValue <= 100) {
                    $('.segment.moderate').addClass('active');
                } else if (aqiValue <= 150) {
                    $('.segment.poor').addClass('active');
                } else if (aqiValue <= 200) {
                    $('.segment.unhealthy').addClass('active');
                } else if (aqiValue <= 300) {
                    $('.segment.severe').addClass('active');
                } else {
                    $('.segment.hazardous').addClass('active');
                }
                
                // Update meter pointer position
                const meterWidth = $('.meter-segments').width();
                const maxAQI = 300; // Maximum AQI value on the scale
                const pointerPosition = Math.min((aqiValue / maxAQI) * meterWidth, meterWidth);
                $('.meter-pointer').css('left', pointerPosition + 'px');
                
                // Update weather information
                if (response.weather) {
                    $('#temperature').text(response.weather.temp);
                    $('#weather-desc').text(response.weather.description);
                    $('#humidity').text(response.weather.humidity);
                    $('#wind-speed').text(response.weather.wind_speed);
                    $('#uv-index').text(response.weather.uvi || 'N/A');
                }
                
                // Update pollutant values
                $('#pm10-value').text(response['PM10'].toFixed(1));
                $('#pm25-value').text(response['PM2.5'].toFixed(1));
                $('#no2-value').text(response['NO2'].toFixed(1));
                $('#o3-value').text(response['O3'].toFixed(1));
                $('#so2-value').text(response['SO2'].toFixed(1));
                $('#co-value').text(response['CO'].toFixed(1));
                $('#nh3-value').text(response['NH3'].toFixed(1));
                
                // Update traffic data with the new AQI value
                updateTrafficData(lat, lon, aqiValue);
                
                // Add animation classes
                $('.aqi-container').addClass('animate__animated animate__fadeIn');
                setTimeout(() => {
                    $('.aqi-container').removeClass('animate__animated animate__fadeIn');
                }, 1000);
            },
            error: function() {
                alert('An error occurred while processing your request.');
            }
        });
    });
});