// Analytics page JavaScript
function formatCurrency(amount, currency) {
    const currencySymbols = {
        'USD': '$',
        'KES': 'KSh',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'AUD': 'A$',
        'CAD': 'C$',
        'JPY': '¥'
    };
    const symbol = currencySymbols[currency] || '$';
    return `${symbol}${amount.toFixed(2)}`;
}

const sales = window.monthlySales;
const itemStats = window.itemStats;
const itemLabels = Object.keys(itemStats);

// Register the datalabels plugin globally (if not already registered by script tag)
Chart.register(ChartDataLabels);

function showSpinner(show) {
    document.getElementById('spinnerOverlay').style.display = show ? 'flex' : 'none';
}

function loadAnalytics(view) {
    showSpinner(true);
    // Remove active class from all buttons
    $('.btn-outline-primary[onclick^="loadAnalytics"]').removeClass('active');
    // Add active class to the clicked button
    $(`.btn-outline-primary[onclick*="loadAnalytics('${view}')"]`).addClass('active');

    // Also, ensure the date range picker is not visually active if a preset is selected
    $('#daterange').removeClass('active-range');
    $('#rangeForm button[type="submit"]').removeClass('active');

    $.get(`/analytics?view=${view}`, data => {
        // The backend now returns JSON for AJAX requests
        console.log("[DEBUG] AJAX response data:", data);
        window.monthlySales = data.monthly_sales;
        window.itemStats = data.item_stats;
        window.currentView = view; // Store the current view

        console.log("[DEBUG] window.monthlySales after update:", window.monthlySales);

        renderAllCharts();
        showSpinner(false);
    });
}

function renderItemChart(type) {
    console.log(`[DEBUG] Rendering item chart for type: ${type}`);
    console.log('[DEBUG] Current itemStats:', window.itemStats);
    
    const data = itemLabels.map(item => itemStats[item][type]);
    console.log(`[DEBUG] Chart data for ${type}:`, data);
    
    const ctx = document.getElementById('itemChart').getContext('2d');

    // Destroy existing chart if it exists
    const existingChart = Chart.getChart('itemChart');
    if (existingChart) {
        console.log('[DEBUG] Destroying existing chart via Chart.getChart');
        existingChart.destroy();
    }

    window.itemChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: itemLabels,
            datasets: [{
                label: type === 'quantity' ? 'Quantity Sold' : 'Revenue',
                data: data,
                backgroundColor: [
                    '#007bff', '#28a745', '#ffc107', '#dc3545',
                    '#17a2b8', '#6f42c1', '#fd7e14', '#20c997'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            animation: { duration: 700 },
            plugins: {
                title: {
                    display: true,
                    text: type === 'quantity' ? 'Top-Selling Items by Quantity' : 'Top-Selling Items by Revenue'
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.label}: ${type === 'quantity' ? ctx.parsed.y : '$' + ctx.parsed.y.toFixed(2)}`
                    }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    formatter: function(value, context) {
                        return type === 'quantity' ? value : '$' + value.toFixed(2);
                    },
                    color: 'black',
                    display: function(context) {
                        // Only display if the value is greater than 0
                        return context.dataset.data[context.dataIndex] > 0;
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return type === 'quantity' ? value : '$' + value;
                        }
                    }
                }
            }
        }
    });
    console.log('[DEBUG] Chart rendered successfully');
}

function renderPieChart(canvasId, label, dataMap, formatter) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const values = itemLabels.map(item => dataMap[item]);
    const total = values.reduce((a, b) => a + b, 0);
    const chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: itemLabels,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: [
                    '#007bff', '#28a745', '#ffc107', '#dc3545',
                    '#17a2b8', '#6f42c1', '#fd7e14', '#20c997'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: { duration: 700 },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 15,
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: label === 'Revenue Share' ? 'Top-Selling Items by Revenue' : 'Top-Selling Items by Quantity'
                },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const value = ctx.parsed;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${ctx.label}: ${formatter(value)} (${percentage}%)`;
                        }
                    }
                },
                datalabels: {
                    formatter: (value, context) => {
                        const percentage = ((value / total) * 100).toFixed(1);
                        return percentage + '%';
                    },
                    color: 'white',
                    textShadowBlur: 4,
                    textShadowColor: 'black',
                    display: function(context) {
                         // Only display if the percentage is greater than a small threshold
                         const percentage = ((context.dataset.data[context.dataIndex] / total) * 100).toFixed(1);
                         return percentage > 5; // Only show percentage if it's more than 5%
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return label === 'Revenue Share' ? formatCurrency(value, userCurrency) : value;
                        }
                    }
                }
            }
        }
    });
    // Assign the created chart to the window variable for later destruction
    if (canvasId === 'revenuePieChart') {
        window.revenuePieChart = chart;
    } else if (canvasId === 'quantityPieChart') {
        window.quantityPieChart = chart;
    }
}

function renderAllCharts() {
    // Destroy existing charts if they exist using their canvas IDs
    const existingItemChart = Chart.getChart('itemChart');
    if (existingItemChart) existingItemChart.destroy();

    const existingRevenuePieChart = Chart.getChart('revenuePieChart');
    if (existingRevenuePieChart) existingRevenuePieChart.destroy();

    const existingQuantityPieChart = Chart.getChart('quantityPieChart');
    if (existingQuantityPieChart) existingQuantityPieChart.destroy();

    const existingRevenueChart = Chart.getChart('revenueChart');
    if (existingRevenueChart) existingRevenueChart.destroy();

    const itemLabels = Object.keys(window.itemStats);

    if (typeof window.itemStats !== 'undefined' && Object.keys(window.itemStats).length > 0) {
        // Render Item Chart (Quantity/Revenue)
        const itemChartCtx = document.getElementById('itemChart').getContext('2d');
        const quantityData = itemLabels.map(item => window.itemStats[item]['quantity']);
        const itemChart = new Chart(itemChartCtx, {
            type: 'bar',
            data: {
                labels: itemLabels,
                datasets: [{
                    label: 'Quantity Sold',
                    data: quantityData,
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545',
                        '#17a2b8', '#6f42c1', '#fd7e14', '#20c997'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 700 },
                plugins: {
                    title: { display: true, text: 'Top-Selling Items by Quantity' },
                    tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed.y}` } },
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        formatter: function(value, context) { return value; },
                        color: 'black',
                        display: function(context) { return context.dataset.data[context.dataIndex] > 0; }
                    }
                },
                scales: { y: { beginAtZero: true, ticks: { callback: function(value) { return value; } } } }
            }
        });

        // Render Revenue Pie Chart
        const revenuePieCtx = document.getElementById('revenuePieChart').getContext('2d');
        const revenuePieData = itemLabels.map(item => window.itemStats[item]['revenue']);
        const totalRevenue = revenuePieData.reduce((a, b) => a + b, 0);
        const revenuePieChart = new Chart(revenuePieCtx, {
            type: 'pie',
            data: {
                labels: itemLabels,
                datasets: [{
                    label: 'Revenue Share',
                    data: revenuePieData,
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545',
                        '#17a2b8', '#6f42c1', '#fd7e14', '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: { duration: 700 },
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 15, padding: 15 } },
                    title: { display: true, text: 'Top-Selling Items by Revenue' },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const value = ctx.parsed;
                                const percentage = ((value / totalRevenue) * 100).toFixed(1);
                                return `${ctx.label}: $${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        formatter: (value, context) => { const percentage = ((value / totalRevenue) * 100).toFixed(1); return percentage + '%'; },
                        color: 'white',
                        textShadowBlur: 4,
                        textShadowColor: 'black',
                        display: function(context) { const percentage = ((context.dataset.data[context.dataIndex] / totalRevenue) * 100).toFixed(1); return percentage > 5; }
                    }
                }
            }
        });

        // Render Quantity Pie Chart
        const quantityPieCtx = document.getElementById('quantityPieChart').getContext('2d');
        const quantityPieData = itemLabels.map(item => window.itemStats[item]['quantity']);
        const totalQuantity = quantityPieData.reduce((a, b) => a + b, 0);
        const quantityPieChart = new Chart(quantityPieCtx, {
            type: 'pie',
            data: {
                labels: itemLabels,
                datasets: [{
                    label: 'Quantity Share',
                    data: quantityPieData,
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545',
                        '#17a2b8', '#6f42c1', '#fd7e14', '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: { duration: 700 },
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 15, padding: 15 } },
                    title: { display: true, text: 'Top-Selling Items by Quantity' },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const value = ctx.parsed;
                                const percentage = ((value / totalQuantity) * 100).toFixed(1);
                                return `${ctx.label}: ${value} (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        formatter: (value, context) => { const percentage = ((value / totalQuantity) * 100).toFixed(1); return percentage + '%'; },
                        color: 'white',
                        textShadowBlur: 4,
                        textShadowColor: 'black',
                        display: function(context) { const percentage = ((context.dataset.data[context.dataIndex] / totalQuantity) * 100).toFixed(1); return percentage > 5; }
                    }
                }
            }
        });
    }

    // Find the container and recreate the revenue chart canvas
    const oldCanvas = document.getElementById('revenueChart');
    if (oldCanvas) {
        const revenueChartContainer = oldCanvas.parentElement;
        oldCanvas.remove(); // Remove the old canvas

        // Create a new canvas element
        const newCanvas = document.createElement('canvas');
        newCanvas.id = 'revenueChart';
        if (revenueChartContainer) {
            revenueChartContainer.appendChild(newCanvas); // Append the new canvas to the container

            const revenueCtx = newCanvas.getContext('2d');
            console.log("[DEBUG] Sales data for revenue chart:", window.monthlySales); // Log the data being used
            console.log("[DEBUG] Revenue chart labels:", window.monthlySales.map(row => row.label)); // Log the labels

            let chartConfig = {};

            if (window.currentView === 'monthly') {
                // Configuration for Monthly view (Category Scale)
                chartConfig = {
                    type: 'line',
                    data: {
                        labels: window.monthlySales.map(row => row.label), // Month names
                        datasets: [{
                            label: 'Revenue',
                            data: window.monthlySales.map(row => row.revenue),
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        animation: { duration: 800 },
                        plugins: {
                            legend: { position: 'top' },
                            tooltip: {
                                callbacks: {
                                    label: ctx => formatCurrency(ctx.parsed.y, userCurrency)
                                }
                            }
                        },
                        scales: {
                            x: { // Use category scale for month names
                                type: 'category',
                                title: {
                                    display: true,
                                    text: 'Month'
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Revenue'
                                }
                            }
                        }
                    }
                };
            } else {
                // Configuration for Daily, Weekly, Hourly, Range views (Time Scale)
                chartConfig = {
                    type: 'line',
                    data: {
                        labels: window.monthlySales.map(row => row.label),
                        datasets: [{
                            label: 'Revenue',
                            data: window.monthlySales.map(row => row.revenue),
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        animation: { duration: 800 },
                        plugins: {
                            legend: { position: 'top' },
                            tooltip: {
                                callbacks: {
                                    label: ctx => formatCurrency(ctx.parsed.y, userCurrency)
                                }
                            }
                        },
                        scales: { // Use time scale for date/time data
                            x: {
                                type: 'time',
                                time: {
                                    unit: window.currentView === 'hourly' ? 'hour' : 'day', // Dynamic unit
                                    tooltipFormat: window.currentView === 'hourly' ? 'YYYY-MM-DD HH:mm' : 'YYYY-MM-DD', // Dynamic tooltip format
                                    displayFormats: {
                                        hour: 'MMM DD HH:mm',
                                        day: 'MMM DD'
                                    },
                                    parser: window.currentView === 'hourly' ? 'YYYY-MM-DD HH:mm' : undefined // Explicitly define parser for hourly
                                },
                                title: {
                                    display: true,
                                    text: 'Date'
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Revenue'
                                }
                            }
                        }
                    }
                };
            }

            const revenueChart = new Chart(revenueCtx, chartConfig);
        }
    }
}

function downloadChartImage(canvasId, filename) {
    const link = document.createElement('a');
    link.download = filename + '.png';
    link.href = document.getElementById(canvasId).toDataURL('image/png');
    link.click();
}

// Initialize date range picker
$(function () {
    $('#daterange').daterangepicker({
        locale: { format: 'YYYY-MM-DD' },
        startDate: moment().subtract(7, 'days'),
        endDate: moment()
    });
});

// Initialize form submission handler
$('#rangeForm').on('submit', function(e) {
    e.preventDefault();
    const range = $('#daterange').val();
    showSpinner(true);
    // Remove active class from all preset buttons
    $('.btn-outline-primary[onclick^="loadAnalytics"]').removeClass('active');
    // Mark the date range picker or its apply button as active if needed
    $('#daterange').addClass('active-range');
    $('#rangeForm button[type="submit"]').addClass('active');

    $.get(`/analytics?view=range&daterange=${range}`, data => {
        const html = $(data).find('#analyticsContent').html();
        $('#analyticsContent').html(html);
        renderAllCharts();
        showSpinner(false);
    });
});

// Function to set the initial active button
function setInitialActiveButton() {
    const urlParams = new URLSearchParams(window.location.search);
    const initialView = urlParams.get('view') || 'monthly';

    window.currentView = initialView; // Set the global currentView variable

    if (initialView === 'range') {
        $('#daterange').addClass('active-range');
        $('#rangeForm button[type="submit"]').addClass('active');
    } else {
        $(`.btn-outline-primary[onclick*="loadAnalytics('${initialView}')"]`).addClass('active');
    }
}

// Initialize on document ready
$(document).ready(function(){
    setInitialActiveButton();
    // Load initial analytics data based on the determined initial view
    const urlParams = new URLSearchParams(window.location.search);
    const initialView = urlParams.get('view') || 'monthly';
    loadAnalytics(initialView);
}); 