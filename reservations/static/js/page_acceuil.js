document.addEventListener('DOMContentLoaded', function () {
    // Graphique pour les cités par wilaya
    const citesParWilayaData = JSON.parse(document.getElementById('terrainsParWilayaData').textContent);
    const wilayas = citesParWilayaData.map(entry => entry.wilaye);
    const nombres = citesParWilayaData.map(entry => entry.nombre);

    const backgroundColors = wilayas.map((_, index) => {
        const colors = [
            'rgba(255, 99, 132, 0.2)',
            'rgba(54, 162, 235, 0.2)',
            'rgba(255, 206, 86, 0.2)',
            'rgba(75, 192, 192, 0.2)',
            'rgba(153, 102, 255, 0.2)',
            'rgba(255, 159, 64, 0.2)',
        ];
        return colors[index % colors.length];
    });

    const borderColors = wilayas.map((_, index) => {
        const colors = [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
        ];
        return colors[index % colors.length];
    });

    var ctx = document.getElementById('citesParWilayaChart').getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: wilayas,
            datasets: [{
                label: 'Nombre de cités par wilaya',
                data: nombres,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1,
                barPercentage: 0.3
            }]
        },
    });

    // Graphique pour les réservations par client
    const reservationsParClientData = JSON.parse(document.getElementById('reservationsParClientData').textContent);
    const clientsData = {};

    reservationsParClientData.forEach(entry => {
        const telephone = entry['terrain__client__numero_telephone'];
        const dateReservation = entry['date_reservation'];
        const nombre = entry['nombre'];

        if (!clientsData[telephone]) {
            clientsData[telephone] = {};
        }

        if (!clientsData[telephone][dateReservation]) {
            clientsData[telephone][dateReservation] = 0;
        }

        clientsData[telephone][dateReservation] += nombre;
    });

    function displayCharts(filteredData) {
        const chartsContainer = document.getElementById('charts-container');
        chartsContainer.innerHTML = '';  // Clear previous charts

        Object.keys(filteredData).forEach((telephone, index) => {
            const dates = Object.keys(filteredData[telephone]);
            const data = dates.map(date => filteredData[telephone][date]);
            const totalReservations = data.reduce((acc, curr) => acc + curr, 0);

            const chartContainer = document.createElement('div');
            chartContainer.classList.add('chart-container');
            chartContainer.innerHTML = `
                <b>Nombre total de réservations :</b> ${totalReservations}
                <canvas id="chart-${telephone}"></canvas><br>
            `;
            chartsContainer.appendChild(chartContainer);

            const ctx = document.getElementById(`chart-${telephone}`).getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: dates,
                    datasets: [{
                        label: `Nombre de réservations pour ${telephone}`,
                        data: data,
                        backgroundColor: backgroundColors[index % backgroundColors.length],
                        borderColor: borderColors[index % borderColors.length],
                        borderWidth: 1,
                        barPercentage: 0.3
                    }]
                },
                options: {
                    scales: {
                        x: {
                            title: {
                                display: false,
                                text: 'Date de Réservation'
                            }
                        },
                        y: {
                            title: {
                                display: false,
                                text: 'Nombre de Réservations'
                            }
                        }
                    }
                }
            });
        });
    }

    displayCharts(clientsData);

    window.filterCharts = function() {
        const input = document.getElementById('phoneNumber').value;
        const filteredData = {};

        Object.keys(clientsData).forEach(telephone => {
            if (telephone.includes(input)) {
                filteredData[telephone] = clientsData[telephone];
            }
        });

        displayCharts(filteredData);
    };
});
