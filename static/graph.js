document.addEventListener('DOMContentLoaded', async () => {
    const cyElement = document.getElementById('cy');
    if (!cyElement) return;

    try {
        const response = await fetch('/graph/data');
        const data = await response.json();

        // Cytoscape initialized with the retrieved data
        const cy = cytoscape({
            container: cyElement,
            elements: data,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#33ff33',
                        'label': 'data(title)',
                        'color': '#ffffff',
                        'text-valign': 'center',
                        'text-halign': 'right',
                        'text-outline-color': '#000000',
                        'text-outline-width': 2,
                        'font-family': 'Share Tech Mono',
                        'width': 20,
                        'height': 20
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#115511',
                        'target-arrow-color': '#115511',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'opacity': 0.6
                    }
                },
                {
                    selector: 'node:hover',
                    style: {
                        'background-color': '#ffffff',
                        'box-shadow': '0 0 20px #33ff33',
                        'width': 30,
                        'height': 30
                    }
                }
            ],
            layout: {
                name: 'cose',
                animate: true,
                padding: 50
            }
        });

        // Double click to open document
        cy.on('tap', 'node', function(evt){
            var node = evt.target;
            window.open('/doc/' + node.id(), '_blank');
        });

    } catch (err) {
        console.error("Failed to load graph data", err);
    }
});
