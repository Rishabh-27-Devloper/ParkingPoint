// Global variables
let currentStep = 1;
let selectedParkingLot = null;
let selectedSlot = null;
let selectedVehicle = null;
let bookingData = {};

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

function initializePage() {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('entry-date').min = today;
    document.getElementById('exit-date').min = today;

    // Set default entry date to today
    document.getElementById('entry-date').value = today;

    // Add event listeners
    document.getElementById('entry-date').addEventListener('change', validateDateTime);
    document.getElementById('entry-time').addEventListener('change', validateDateTime);
    document.getElementById('exit-date').addEventListener('change', validateDateTime);
    document.getElementById('exit-time').addEventListener('change', validateDateTime);

    // Initialize first step
    setStepActive(1);
    document.getElementById('next-btn').disabled = true;
}

function selectParkingLot(event, lotId, lotName, rate) {
    // Remove previous selection
    document.querySelectorAll('.parking-lot-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Select current lot
    if (event && event.target) {
        let card = event.target.closest('.parking-lot-card');
        if (card) card.classList.add('selected');
    }

    selectedParkingLot = {
        id: lotId,
        name: lotName,
        rate: rate
    };

    // Enable next button
    document.getElementById('next-btn').disabled = false;
}

function generateParkingSlots() {
    const parkingGrid = document.getElementById('parking-grid');
    parkingGrid.innerHTML = '';

    // Generate slots PA1-PA9, PB1-PB9, ..., PZ1-PZ9
    const rows = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const totalRows = 10; // For demo, show 4 rows (A-D)
    const slotsPerRow = 9;
    const occupiedSlots = getRandomOccupiedSlots(); // Simulate some occupied slots

    for (let r = 0; r < totalRows; r++) {
        for (let s = 1; s <= slotsPerRow; s++) {
            const slotId = `P${rows[r]}${s}`;
            const slotDiv = document.createElement('div');
            slotDiv.className = 'parking-slot';
            slotDiv.textContent = slotId;
            slotDiv.dataset.slotId = slotId;

            if (occupiedSlots.includes(slotId)) {
                slotDiv.classList.add('occupied');
            } else {
                slotDiv.onclick = function() { selectSlot(slotId, slotDiv); };
            }

            if (selectedSlot === slotId) {
                slotDiv.classList.add('selected');
            }

            parkingGrid.appendChild(slotDiv);
        }
    }
}

function getRandomOccupiedSlots() {
    // For demo, randomly occupy 6 slots
    const slots = [];
    const rows = 'ABCD';
    while (slots.length < 6) {
        const row = rows[Math.floor(Math.random() * rows.length)];
        const num = Math.floor(Math.random() * 9) + 1;
        const slot = `P${row}${num}`;
        if (!slots.includes(slot)) slots.push(slot);
    }
    return slots;
}

function selectSlot(slotId, slotDiv) {
    // Deselect previous
    document.querySelectorAll('.parking-slot.selected').forEach(el => el.classList.remove('selected'));
    slotDiv.classList.add('selected');
    selectedSlot = slotId;
    document.getElementById('selected-slot-info').classList.remove('hidden');
    document.getElementById('selected-slot-display').textContent = slotId;
    document.getElementById('next-btn').disabled = false;
}

function selectVehicle(event, vehicleId, number, model) {
    // Remove previous selection
    document.querySelectorAll('.vehicle-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Select current vehicle
    if (event && event.target) {
        let card = event.target.closest('.vehicle-card');
        if (card) card.classList.add('selected');
    }

    selectedVehicle = {
        id: vehicleId,
        number: number,
        model: model
    };

    // Show selected vehicle info
    document.getElementById('selected-vehicle-info').classList.remove('hidden');
    document.getElementById('selected-vehicle-display').textContent = `${model} (${number})`;
    
    // Enable book button
    document.getElementById('book-btn').disabled = false;
}

function setStepActive(step) {
    document.querySelectorAll('.step').forEach((el, idx) => {
        el.classList.remove('active', 'completed');
        if (idx + 1 < step) {
            el.classList.add('completed');
        } else if (idx + 1 === step) {
            el.classList.add('active');
        }
    });
}

function nextStep() {
    if (currentStep === 1 && selectedParkingLot) {
        // Go to slot selection
        document.getElementById('location-section').classList.add('hidden');
        document.getElementById('slot-section').classList.add('active');
        setStepActive(2);
        currentStep = 2;
        
        // Generate parking slots when entering step 2
        generateParkingSlots();
        
        document.getElementById('next-btn').disabled = true;
        document.getElementById('back-btn').classList.remove('hidden');
        
    } else if (currentStep === 2 && selectedSlot) {
        // Go to datetime selection
        document.getElementById('slot-section').classList.remove('active');
        document.getElementById('datetime-section').classList.remove('hidden');
        setStepActive(3);
        currentStep = 3;
        document.getElementById('next-btn').disabled = true;
        
    } else if (currentStep === 3 && validateDateTime()) {
        // Go to vehicle/payment selection
        document.getElementById('datetime-section').classList.add('hidden');
        document.getElementById('payment-section').classList.remove('hidden');
        setStepActive(4);
        currentStep = 4;
        document.getElementById('next-btn').classList.add('hidden');
        document.getElementById('book-btn').classList.remove('hidden');
        document.getElementById('book-btn').disabled = true; // Disable until vehicle is selected
    }
}

function goBack() {
    if (currentStep === 2) {
        // Go back to location selection
        document.getElementById('slot-section').classList.remove('active');
        document.getElementById('location-section').classList.remove('hidden');
        setStepActive(1);
        currentStep = 1;
        document.getElementById('back-btn').classList.add('hidden');
        document.getElementById('next-btn').disabled = !selectedParkingLot;
        
    } else if (currentStep === 3) {
        // Go back to slot selection
        document.getElementById('datetime-section').classList.add('hidden');
        document.getElementById('slot-section').classList.add('active');
        setStepActive(2);
        currentStep = 2;
        document.getElementById('next-btn').disabled = !selectedSlot;
        
    } else if (currentStep === 4) {
        // Go back to datetime selection
        document.getElementById('payment-section').classList.add('hidden');
        document.getElementById('datetime-section').classList.remove('hidden');
        setStepActive(3);
        currentStep = 3;
        document.getElementById('next-btn').classList.remove('hidden');
        document.getElementById('book-btn').classList.add('hidden');
        document.getElementById('next-btn').disabled = !validateDateTime();
    }
}

function validateDateTime() {
    const entryDate = document.getElementById('entry-date').value;
    const entryTime = document.getElementById('entry-time').value;
    const exitDate = document.getElementById('exit-date').value;
    const exitTime = document.getElementById('exit-time').value;
    let valid = true;

    // Hide all error messages first
    document.getElementById('entry-error').style.display = 'none';
    document.getElementById('exit-error').style.display = 'none';

    // Validate entry date and time
    if (!entryDate || !entryTime) {
        document.getElementById('entry-error').style.display = 'block';
        valid = false;
    }

    // Validate exit date and time
    if (!exitDate || !exitTime) {
        document.getElementById('exit-error').style.display = 'block';
        valid = false;
    }

    if (valid) {
        const entry = new Date(`${entryDate}T${entryTime}`);
        const exit = new Date(`${exitDate}T${exitTime}`);
        const now = new Date();

        // Check if entry time is in the past (only for today's date)
        if (entryDate === new Date().toISOString().split('T')[0] && entry < now) {
            document.getElementById('entry-error').textContent = 'Entry time cannot be in the past';
            document.getElementById('entry-error').style.display = 'block';
            valid = false;
        }

        // Check if exit time is after entry time
        if (exit <= entry) {
            document.getElementById('exit-error').textContent = 'Exit time must be after entry time';
            document.getElementById('exit-error').style.display = 'block';
            valid = false;
        }

        if (valid) {
            // Calculate duration and update pricing
            const durationMs = exit - entry;
            const durationHours = Math.ceil(durationMs / (1000 * 60 * 60));
            
            // Show duration
            document.getElementById('duration-display').classList.remove('hidden');
            document.getElementById('duration-text').textContent = `${durationHours} hour${durationHours > 1 ? 's' : ''}`;
            
            // Update pricing
            updatePricing(durationHours);
            
            // Enable next button
            document.getElementById('next-btn').disabled = false;
        }
    }

    if (!valid) {
        document.getElementById('duration-display').classList.add('hidden');
        document.getElementById('pricing-summary').classList.add('hidden');
        document.getElementById('next-btn').disabled = true;
    }

    return valid;
}

function updatePricing(hours) {
    if (!selectedParkingLot) return;

    const rate = selectedParkingLot.rate;
    const subtotal = rate * hours;
    const tax = Math.round(subtotal * 0.18);
    const total = subtotal + tax;

    // Show pricing summary
    document.getElementById('pricing-summary').classList.remove('hidden');
    document.getElementById('hourly-rate').textContent = `₹${rate}/hr`;
    document.getElementById('duration-hours').textContent = `${hours} hour${hours > 1 ? 's' : ''}`;
    document.getElementById('subtotal').textContent = `₹${subtotal}`;
    document.getElementById('tax-amount').textContent = `₹${tax}`;
    document.getElementById('total-amount').innerHTML = `<strong>₹${total}</strong>`;
}

function bookParking() {
    if (!selectedParkingLot || !selectedSlot || !selectedVehicle) {
        alert('Please complete all steps before booking.');
        return;
    }

    // Validate datetime one more time
    if (!validateDateTime()) {
        alert('Please select valid entry and exit times.');
        return;
    }

    // Collect all booking data
    const entryDateTime = new Date(`${document.getElementById('entry-date').value}T${document.getElementById('entry-time').value}`);
    const exitDateTime = new Date(`${document.getElementById('exit-date').value}T${document.getElementById('exit-time').value}`);
    const durationHours = Math.ceil((exitDateTime - entryDateTime) / (1000 * 60 * 60));
    const subtotal = selectedParkingLot.rate * durationHours;
    const tax = Math.round(subtotal * 0.18);
    const total = subtotal + tax;

    bookingData = {
        parkingLot: selectedParkingLot,
        slot: selectedSlot,
        vehicle: selectedVehicle,
        entryDateTime: entryDateTime.toISOString(),
        exitDateTime: exitDateTime.toISOString(),
        duration: durationHours,
        pricing: {
            hourlyRate: selectedParkingLot.rate,
            subtotal: subtotal,
            tax: tax,
            total: total
        }
    };

    // For demo purposes, show confirmation
    const confirmationMessage = `
Booking Summary:
- Location: ${selectedParkingLot.name}
- Slot: ${selectedSlot}
- Vehicle: ${selectedVehicle.model} (${selectedVehicle.number})
- Entry: ${entryDateTime.toLocaleString()}
- Exit: ${exitDateTime.toLocaleString()}
- Duration: ${durationHours} hour${durationHours > 1 ? 's' : ''}
- Total Amount: ₹${total}

Proceed to payment?
    `;

    if (confirm(confirmationMessage)) {
        // Create a form and submit it to /create_order with POST
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/create_order';
        form.style.display = 'none';

        // Add total amount
        const amountInput = document.createElement('input');
        amountInput.type = 'hidden';
        amountInput.name = 'amount';
        amountInput.value = bookingData.pricing.total;
        form.appendChild(amountInput);

        // Add booking data as JSON string
        const bookingInput = document.createElement('input');
        bookingInput.type = 'hidden';
        bookingInput.name = 'booking';
        bookingInput.value = JSON.stringify(bookingData);
        form.appendChild(bookingInput);

        document.body.appendChild(form);
        form.submit();
    }
}

// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}