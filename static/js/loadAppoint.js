// Global state variables
let currentAppointmentId = null;
let currentAppointmentData = null;
let selectedRating = 0;

// Helper to safely access global variables defined in HTML
const getIsServicer = () => (typeof isServicer !== 'undefined' ? isServicer : false);
const getCurrentServicerId = () => (typeof currentServicerId !== 'undefined' ? currentServicerId : null);

// Get CSRF Token for AJAX requests
function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput && csrfInput.value) return csrfInput.value;
    
    // Fallback: Parse from cookie
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue || '';
}

// ==========================================
// MAIN FUNCTION: View Appointment Details
// ==========================================
window.loadAppointmentDetails = window.viewAppointmentDetails = function(appointmentId) {
    currentAppointmentId = appointmentId;

    // 1. Reset Modal UI
    resetModalUI();

    // 2. Fetch Data
    fetch(`/api/appointments/${appointmentId}/`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch appointment details');
            return response.json();
        })
        .then(data => {
            currentAppointmentData = data;
            populateBasicInfo(data);
            populateServicerDetails(data);
            populatePricingDetails(data);
            populateOTPSection(data);
            populateRatingSection(data);
            populateImages(data);
            populateBargaining(data);
        })
        .catch(error => {
            console.error('Error fetching details:', error);
            alert('Failed to load appointment details. Please try again.');
        });
};

// ==========================================
// UI POPULATION HELPERS
// ==========================================

function resetModalUI() {
    const detailImages = document.getElementById('detail-images');
    if (detailImages) detailImages.innerHTML = '';
    
    const bargainHistory = document.getElementById('bargainHistory');
    if (bargainHistory) bargainHistory.innerHTML = '';

    // Hide sections by default
    ['servicerDetailsSection', 'totalPriceSection', 'paymentSection', 'paymentSuccessSection', 'otpSection', 'ratingSection']
        .forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
}

function populateBasicInfo(data) {
    setText('detail-issue', data.issue === 'others' ? data.custom_issue : data.issue_display);
    setText('detail-booking-id', data.booking_id || data.id);
    setText('detail-booking', data.booking_id || data.id);
    
    const formattedDate = data.expected_time ? new Date(data.expected_time).toLocaleString() : 'N/A';
    setText('detail-date', formattedDate);
    setText('detail-time', formattedDate);
    
    setText('detail-amount', '₹' + parseFloat(data.expected_amount).toFixed(2));
    setText('detail-description', data.description);
    
    const locationText = data.address ? `${data.address}, ${data.city || ''}, ${data.state || ''}` : `${data.city || ''}, ${data.state || ''}`;
    setText('detail-location', locationText);

    setText('detail-customer', data.full_name);
    setText('detail-contact', data.contact_number);

    const statusBadge = document.getElementById('detail-status');
    if (statusBadge) {
        statusBadge.textContent = (data.status || '').toUpperCase();
        statusBadge.className = `badge bg-${getStatusColor(data.status)}`;
    }
}

function populateServicerDetails(data) {
    const section = document.getElementById('servicerDetailsSection');
    if (!section) return;

    if (data.servicer_details) {
        setText('servicer-id', data.servicer_details.id);
        setText('servicer-name', data.servicer_details.full_name);
        setText('servicer-mobile', data.servicer_details.mobile_number);
        setText('servicer-whatsapp', data.servicer_details.whatsapp_number);
        setText('servicer-address', data.servicer_details.address);
        setText('servicer-rating', (data.servicer_details.rating ? data.servicer_details.rating : '0.0') + ' ★');
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
}

function populatePricingDetails(data) {
    const section = document.getElementById('totalPriceSection');
    if (!section) return;

    if (data.status === 'accepted' || data.status === 'completed') {
        setText('final-agreed-price', '₹' + parseFloat(data.expected_amount).toFixed(2));
        setText('distance-cost', data.distance_cost || '₹0.00');
        
        const customerBlock = document.getElementById('customerPriceBlock');
        const servicerBlock = document.getElementById('servicerPriceBlock');
        
        if (!getIsServicer()) {
            if (customerBlock) customerBlock.style.display = 'block';
            if (servicerBlock) servicerBlock.style.display = 'none';
            setText('platform-fee-user', data.platform_fee_user || '₹0.00');
            setText('user-total-price', data.user_total_price || '₹0.00');
        } else {
            if (customerBlock) customerBlock.style.display = 'none';
            if (servicerBlock) servicerBlock.style.display = 'block';
            setText('platform-fee-servicer', data.platform_fee_servicer || '₹0.00');
            setText('servicer-earnings', data.servicer_earnings || '₹0.00');
        }
        
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
}

function populateOTPSection(data) {
    const section = document.getElementById('otpSection');
    const otpDisplay = document.getElementById('otpDisplay');
    const otpVerification = document.getElementById('otpVerification');
    
    const paymentSection = document.getElementById('paymentSection');
    const paymentSuccessSection = document.getElementById('paymentSuccessSection');
    const paymentRefId = document.getElementById('paymentRefId');
    const payNowBtn = document.getElementById('payNowBtn');

    if (!section) return;

    if (!getIsServicer()) {
        // Customer View:
        if (data.payment_status === 'paid') {
            if (paymentSection) paymentSection.style.display = 'none';
            if (paymentSuccessSection) {
                paymentSuccessSection.style.display = 'block';
                if (paymentRefId) paymentRefId.textContent = data.razorpay_payment_id || 'Paid Online';
                const viewInvoiceBtn = document.getElementById('viewInvoiceBtn');
                if (viewInvoiceBtn) viewInvoiceBtn.href = `/invoice/${data.id}/`;
            }
            
            if (data.otp && !data.otp_verified) {
                section.style.display = 'block';
                if (otpDisplay) {
                    otpDisplay.style.display = 'block';
                    setText('generated-otp', data.otp || '------');
                }
                if (otpVerification) otpVerification.style.display = 'none';
            } else {
                section.style.display = 'none';
            }
        } else {
            // Unpaid appointment:
            if (data.status !== 'cancelled') {
                if (paymentSection) {
                    paymentSection.style.display = 'block';
                    if (payNowBtn) {
                        payNowBtn.disabled = false;
                        payNowBtn.innerHTML = '<i class="fas fa-credit-card me-1"></i> Pay Now';
                    }
                }
            } else {
                if (paymentSection) paymentSection.style.display = 'none';
            }
            if (paymentSuccessSection) paymentSuccessSection.style.display = 'none';
            section.style.display = 'none';
        }
    } else {
        // Servicer View:
        if (paymentSection) paymentSection.style.display = 'none';
        if (paymentSuccessSection) {
            if (data.payment_status === 'paid') {
                paymentSuccessSection.style.display = 'block';
                if (paymentRefId) paymentRefId.textContent = data.razorpay_payment_id || 'Paid Online';
            } else {
                paymentSuccessSection.style.display = 'none';
            }
        }

        if (data.status === 'accepted' && !data.otp_verified) {
            section.style.display = 'block';
            if (otpDisplay) otpDisplay.style.display = 'none';

            if (data.payment_status === 'paid') {
                if (otpVerification) {
                    otpVerification.style.display = 'block';
                    otpVerification.innerHTML = `
                        <p class="mb-2">Enter the 6-digit OTP provided by the customer to mark the job complete:</p>
                        <div class="input-group" style="max-width: 300px;">
                            <input type="text" class="form-control otp-input" id="servicer-otp-input" maxlength="6" placeholder="6-Digit OTP">
                            <button class="btn btn-success" onclick="verifyOtp()"><i class="fas fa-check-circle me-1"></i> Verify OTP</button>
                        </div>
                    `;
                }
            } else {
                if (otpVerification) {
                    otpVerification.style.display = 'block';
                    otpVerification.innerHTML = `
                        <div class="alert alert-warning mb-0">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>Awaiting Customer Payment</strong><br>
                            The customer must complete online payment before service completion & OTP verification can occur.
                        </div>
                    `;
                }
            }
        } else {
            section.style.display = 'none';
        }
    }
}

function populateRatingSection(data) {
    const section = document.getElementById('ratingSection');
    const submitBtn = document.getElementById('submitRatingBtn');
    const msgElem = document.getElementById('rating-message');

    if (!section) return;

    if (data.status === 'completed' && !getIsServicer() && data.servicer_details) {
        section.style.display = 'block';
        if (submitBtn) submitBtn.disabled = false;
        if (msgElem) msgElem.style.display = 'none';

        if (data.appointment_rating) {
            setupRatingStars(data.appointment_rating);
            if (submitBtn) submitBtn.disabled = true;
            if (msgElem) {
                msgElem.textContent = `You rated this service: ${data.appointment_rating} Stars ★`;
                msgElem.className = 'text-success mt-2 fw-bold';
                msgElem.style.display = 'block';
            }
        } else {
            setupRatingStars(0);
        }
    } else {
        section.style.display = 'none';
    }
}

function populateImages(data) {
    const gallery = document.getElementById('detail-images');
    if (!gallery) return;

    const images = [data.image1, data.image2, data.image3, data.image4]
        .filter(img => img && img !== '');

    if (images.length > 0) {
        gallery.innerHTML = '';
        images.forEach(imgUrl => {
            const img = document.createElement('img');
            img.src = imgUrl;
            img.className = 'img-thumbnail me-2 mb-2';
            img.style.width = '100px';
            img.style.height = '100px';
            img.style.objectFit = 'cover';
            img.style.cursor = 'pointer';
            img.onclick = () => window.open(imgUrl, '_blank');
            gallery.appendChild(img);
        });
    } else {
        gallery.innerHTML = '<p class="text-muted small">No images uploaded.</p>';
    }
}

function populateBargaining(data) {
    // 1. Render History
    renderBargainHistory(data.bargaining_history || [], data.status);

    // 2. Configure Negotiation Action Buttons in Modal
    const bargainBtn = document.getElementById('bargainButton') || document.getElementById('makeOfferBtn');
    const acceptBtn = document.getElementById('acceptAppointmentBtn');

    if (bargainBtn) {
        if (data.status === 'pending') {
            bargainBtn.style.display = 'inline-block';
            bargainBtn.onclick = function() {
                openBargainModal(data.id, data.expected_amount);
            };
        } else {
            bargainBtn.style.display = 'none';
        }
    }

    if (acceptBtn) {
        if (data.status === 'pending' && getIsServicer()) {
            acceptBtn.style.display = 'inline-block';
            acceptBtn.textContent = `Accept Initial Price (₹${parseFloat(data.expected_amount).toFixed(2)})`;
            acceptBtn.onclick = function() {
                acceptAppointmentConfirmation(data.id);
            };
        } else {
            acceptBtn.style.display = 'none';
        }
    }
}

// ==========================================
// PRICE NEGOTIATION / BARGAINING WORKFLOW
// ==========================================

window.openBargainModal = function(appointmentId, currentBudget) {
    currentAppointmentId = appointmentId || currentAppointmentId;
    const targetBudget = currentBudget || (currentAppointmentData ? currentAppointmentData.expected_amount : '');
    
    const initialPriceInput = document.getElementById('initialPrice');
    const offerPriceInput = document.getElementById('offerPrice');
    const offerMessageInput = document.getElementById('offerMessage');

    if (initialPriceInput) {
        initialPriceInput.value = targetBudget ? `₹${parseFloat(targetBudget).toFixed(2)}` : '';
    }
    if (offerPriceInput) {
        offerPriceInput.value = '';
    }
    if (offerMessageInput) {
        offerMessageInput.value = '';
    }

    // Show Bargain Modal using Bootstrap 5
    const modalEl = document.getElementById('bargainModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
        setTimeout(() => {
            if (offerPriceInput) offerPriceInput.focus();
        }, 400);
    }
};

window.submitBargain = function() {
    const priceInput = document.getElementById('offerPrice');
    const msgInput = document.getElementById('offerMessage');
    
    if (!priceInput || !priceInput.value || parseFloat(priceInput.value) <= 0) {
        alert('Please enter a valid counter-offer price greater than 0.');
        if (priceInput) priceInput.focus();
        return;
    }

    const offerAmount = parseFloat(priceInput.value);
    const payload = {
        appointment_id: currentAppointmentId,
        message: msgInput ? msgInput.value.trim() : '',
        [getIsServicer() ? 'servicer_offer' : 'user_offer']: offerAmount
    };

    fetch('/api/bargain/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Your counter-offer has been submitted successfully!');
            // Close Bargain Modal
            const modalEl = document.getElementById('bargainModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.hide();
            }
            // Refresh appointment details modal
            window.loadAppointmentDetails(currentAppointmentId);
        } else {
            alert('Error: ' + (data.error || 'Failed to submit offer'));
        }
    })
    .catch(err => {
        console.error('Bargain submission error:', err);
        alert('An error occurred while submitting your offer. Please try again.');
    });
};

window.acceptOffer = function(bargainId) {
    if (!confirm('Are you sure you want to accept this offer? This will confirm the final appointment price.')) {
        return;
    }

    fetch(`/api/bargain/${bargainId}/accept/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Offer accepted! The appointment has been confirmed at ₹' + data.final_price);
            window.loadAppointmentDetails(currentAppointmentId);
        } else {
            alert('Error: ' + (data.error || 'Failed to accept offer'));
        }
    })
    .catch(err => {
        console.error('Accept offer error:', err);
        alert('Failed to accept offer. Please try again.');
    });
};

window.rejectOffer = function(bargainId) {
    if (!confirm('Are you sure you want to reject this counter-offer?')) {
        return;
    }

    fetch(`/api/bargain/${bargainId}/reject/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Offer rejected.');
            window.loadAppointmentDetails(currentAppointmentId);
        } else {
            alert('Error: ' + (data.error || 'Failed to reject offer'));
        }
    })
    .catch(err => {
        console.error('Reject offer error:', err);
        alert('Failed to reject offer.');
    });
};

window.acceptAppointmentConfirmation = function(appointmentId) {
    const targetId = appointmentId || currentAppointmentId;
    if (!targetId) return;

    if (!confirm('Are you sure you want to accept this appointment at the initial expected amount?')) {
        return;
    }

    fetch(`/api/appointments/${targetId}/accept/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Appointment accepted successfully!');
            const modalEl = document.getElementById('appointmentModal');
            if (modalEl && modalEl.classList.contains('show')) {
                window.loadAppointmentDetails(targetId);
            } else {
                location.reload();
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to accept appointment'));
        }
    })
    .catch(err => {
        console.error('Accept appointment error:', err);
        alert('Failed to accept appointment.');
    });
};

function renderBargainHistory(history, appointmentStatus) {
    const container = document.getElementById('bargainHistory');
    if (!container) return;

    if (!history || history.length === 0) {
        container.innerHTML = `
            <div class="text-muted small p-3 bg-light rounded text-center">
                <i class="fas fa-handshake me-1"></i> No price negotiations yet.
                ${appointmentStatus === 'pending' ? `
                <div class="mt-2">
                    <button class="btn btn-sm btn-primary" onclick="openBargainModal(${currentAppointmentId})">
                        <i class="fas fa-handshake me-1"></i> Propose Counter Offer
                    </button>
                    ${getIsServicer() ? `
                    <button class="btn btn-sm btn-success ms-1" onclick="acceptAppointmentConfirmation(${currentAppointmentId})">
                        <i class="fas fa-check me-1"></i> Accept Initial Price
                    </button>` : ''}
                </div>` : ''}
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    history.forEach(item => {
        const isServicerOffer = item.offered_by === 'servicer';
        const isMyOffer = (getIsServicer() && isServicerOffer) || (!getIsServicer() && !isServicerOffer);
        const offerPrice = isServicerOffer ? item.servicer_offer_price : item.user_offer_price;
        const initialPrice = parseFloat(item.initial_price || 0).toFixed(2);
        const formattedOfferPrice = offerPrice ? parseFloat(offerPrice).toFixed(2) : '0.00';

        const card = document.createElement('div');
        card.className = `card mb-3 border-${getBargainStatusBorder(item.status)} shadow-sm`;

        let partyLabel = '';
        if (isServicerOffer) {
            const sName = item.servicer_info ? item.servicer_info.full_name : 'Service Provider';
            const sRating = (item.servicer_info && item.servicer_info.rating) ? `(${item.servicer_info.rating} ★)` : '';
            const sIdBadge = (item.servicer_info && item.servicer_info.id) ? `<span class="badge bg-dark text-warning font-monospace ms-1 px-2 py-0.5" style="font-size:0.75rem;">#${item.servicer_info.id}</span>` : '';
            partyLabel = `<i class="fas fa-tools text-primary me-1"></i> <strong>${sName}</strong> ${sIdBadge} <span class="text-warning small">${sRating}</span>`;
        } else {
            partyLabel = `<i class="fas fa-user text-secondary me-1"></i> <strong>Customer Offer</strong>`;
        }

        let statusBadge = `<span class="badge bg-${getBargainStatusBadge(item.status)}">${item.status_display || item.status}</span>`;

        let actionButtons = '';
        if (appointmentStatus === 'pending' && item.status === 'pending') {
            if (!isMyOffer) {
                // Actions for receiving party
                actionButtons = `
                    <div class="mt-3 pt-2 border-top d-flex gap-2 justify-content-end">
                        <button class="btn btn-sm btn-success" onclick="acceptOffer(${item.id})">
                            <i class="fas fa-check me-1"></i> Accept Offer (₹${formattedOfferPrice})
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="rejectOffer(${item.id})">
                            <i class="fas fa-times me-1"></i> Reject
                        </button>
                        <button class="btn btn-sm btn-outline-primary" onclick="openBargainModal(${currentAppointmentId}, ${formattedOfferPrice})">
                            <i class="fas fa-comments me-1"></i> Counter Offer
                        </button>
                    </div>
                `;
            } else {
                // Actions for offering party
                actionButtons = `
                    <div class="mt-2 pt-2 border-top d-flex justify-content-between align-items-center">
                        <small class="text-muted"><i class="fas fa-hourglass-half me-1 text-warning"></i> Waiting for other party's response</small>
                        <button class="btn btn-sm btn-outline-secondary" onclick="openBargainModal(${currentAppointmentId}, ${formattedOfferPrice})">
                            <i class="fas fa-edit me-1"></i> Update Offer
                        </button>
                    </div>
                `;
            }
        }

        card.innerHTML = `
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>${partyLabel}</div>
                    <div>${statusBadge}</div>
                </div>
                <div class="d-flex align-items-center gap-2 mb-2">
                    <span class="text-decoration-line-through text-muted small">₹${initialPrice}</span>
                    <i class="fas fa-arrow-right text-muted small"></i>
                    <span class="fw-bold text-primary fs-5">₹${formattedOfferPrice}</span>
                </div>
                ${item.message ? `<div class="p-2 bg-light rounded text-dark small fst-italic mb-2"><i class="fas fa-comment-dots text-muted me-1"></i>"${item.message}"</div>` : ''}
                <div class="text-muted" style="font-size: 0.75rem;">
                    <i class="far fa-clock me-1"></i> ${new Date(item.created_at).toLocaleString()}
                </div>
                ${actionButtons}
            </div>
        `;

        container.appendChild(card);
    });

    if (appointmentStatus === 'pending') {
        const actionRow = document.createElement('div');
        actionRow.className = 'mt-3 pt-2 text-center';
        actionRow.innerHTML = `
            <button class="btn btn-primary btn-sm me-2" onclick="openBargainModal(${currentAppointmentId})">
                <i class="fas fa-handshake me-1"></i> Propose Counter Offer
            </button>
            ${getIsServicer() ? `
            <button class="btn btn-success btn-sm" onclick="acceptAppointmentConfirmation(${currentAppointmentId})">
                <i class="fas fa-check me-1"></i> Accept Initial Price
            </button>` : ''}
        `;
        container.appendChild(actionRow);
    }
}

function getBargainStatusBadge(status) {
    switch (status) {
        case 'pending': return 'warning text-dark';
        case 'accepted':
        case 'user_accepted':
        case 'servicer_accepted': return 'success';
        case 'rejected': return 'danger';
        default: return 'secondary';
    }
}

function getBargainStatusBorder(status) {
    switch (status) {
        case 'pending': return 'warning';
        case 'accepted':
        case 'user_accepted':
        case 'servicer_accepted': return 'success';
        case 'rejected': return 'danger';
        default: return 'light';
    }
}

// ==========================================
// BOOKMARK WORKFLOW
// ==========================================

window.toggleBookmark = function(button, appointmentId) {
    fetch(`/api/appointments/${appointmentId}/bookmark/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (button) {
                if (data.bookmarked) {
                    button.classList.add('bookmarked');
                } else {
                    button.classList.remove('bookmarked');
                    if (window.location.pathname.includes('bookmarked_appointments')) {
                        const card = button.closest('.appointment-card');
                        if (card) {
                            card.remove();
                            const grid = document.querySelector('.appointments-grid');
                            if (grid && grid.querySelectorAll('.appointment-card').length === 0) {
                                location.reload();
                            }
                        }
                    }
                }
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to update bookmark'));
        }
    })
    .catch(err => {
        console.error('Bookmark error:', err);
    });
};

// ==========================================
// OTP VERIFICATION WORKFLOW
// ==========================================

window.verifyOtp = function() {
    const input = document.getElementById('servicer-otp-input');
    const errorMsg = document.getElementById('otp-error');
    
    if (!input || !input.value.trim()) {
        if (errorMsg) {
            errorMsg.textContent = "Please enter the 6-digit OTP.";
            errorMsg.style.display = 'block';
        }
        return;
    }

    fetch(`/api/appointments/${currentAppointmentId}/verify-otp/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ otp: input.value.trim() })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('OTP Verified Successfully! Job marked as completed.');
            window.loadAppointmentDetails(currentAppointmentId);
        } else {
            if (errorMsg) {
                errorMsg.textContent = data.error || 'Invalid OTP. Please check and try again.';
                errorMsg.style.display = 'block';
            }
        }
    })
    .catch(err => {
        console.error('OTP error:', err);
        alert('Failed to verify OTP. Please try again.');
    });
};

// ==========================================
// RATING SYSTEM WORKFLOW
// ==========================================

function setupRatingStars(initialRating = 0) {
    const container = document.getElementById('servicer-stars');
    if (!container) return;

    container.innerHTML = '';
    selectedRating = initialRating;
    const submitBtn = document.getElementById('submitRatingBtn');
    const isLocked = submitBtn && submitBtn.disabled;

    for (let i = 1; i <= 5; i++) {
        const star = document.createElement('i');
        star.className = (i <= selectedRating) ? 'fas fa-star selected' : 'far fa-star';
        star.style.cursor = isLocked ? 'default' : 'pointer';
        star.style.color = '#ffc107';
        star.style.fontSize = '1.75rem';
        star.style.marginRight = '8px';
        star.setAttribute('data-rating', i);

        if (!isLocked) {
            star.onclick = function() {
                selectedRating = parseInt(this.getAttribute('data-rating'));
                updateStarDisplay();
            };
            star.onmouseover = function() {
                highlightStars(parseInt(this.getAttribute('data-rating')));
            };
            star.onmouseout = updateStarDisplay;
        }
        container.appendChild(star);
    }
}

function updateStarDisplay() {
    const stars = document.querySelectorAll('#servicer-stars i');
    stars.forEach(star => {
        const r = parseInt(star.getAttribute('data-rating'));
        star.className = (r <= selectedRating) ? 'fas fa-star' : 'far fa-star';
    });
}

function highlightStars(rating) {
    const stars = document.querySelectorAll('#servicer-stars i');
    stars.forEach(star => {
        const r = parseInt(star.getAttribute('data-rating'));
        star.className = (r <= rating) ? 'fas fa-star' : 'far fa-star';
    });
}

window.submitRating = function() {
    const msgElem = document.getElementById('rating-message');
    if (selectedRating === 0) {
        if (msgElem) {
            msgElem.textContent = "Please select at least 1 star to rate.";
            msgElem.className = 'text-danger mt-2 fw-bold';
            msgElem.style.display = 'block';
        }
        return;
    }

    fetch(`/api/appointments/${currentAppointmentId}/rate-servicer/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ rating: selectedRating })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (msgElem) {
                msgElem.textContent = "Thank you! Your rating has been submitted.";
                msgElem.className = 'text-success mt-2 fw-bold';
                msgElem.style.display = 'block';
            }
            const submitBtn = document.getElementById('submitRatingBtn');
            if (submitBtn) submitBtn.disabled = true;
            setupRatingStars(selectedRating);
        } else {
            if (msgElem) {
                msgElem.textContent = data.error || 'Failed to submit rating.';
                msgElem.className = 'text-danger mt-2 fw-bold';
                msgElem.style.display = 'block';
            }
        }
    })
    .catch(err => {
        console.error('Rating error:', err);
        alert('Failed to submit rating.');
    });
};

// ==========================================
// ==========================================
// PAYMENT WORKFLOW (RAZORPAY & INSTANT ESCROW)
// ==========================================

window.payNow = window.payNowForAppointment = function(appId, clickedBtn) {
    if (appId) {
        currentAppointmentId = appId;
    }
    
    if (!currentAppointmentId) {
        alert('Please select an appointment first.');
        return;
    }

    const btn = (clickedBtn instanceof HTMLElement ? clickedBtn : null) || 
                (appId ? document.querySelector(`button[onclick*="payNow(${appId}"]`) : null) || 
                document.getElementById('payNowBtn');

    function resetBtn() {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-credit-card me-1"></i> Pay Now';
        }
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Initializing...';
    }

    fetch(`/api/appointments/${currentAppointmentId}/payment/initiate/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to initiate payment');
        return response.json();
    })
    .then(data => {
        resetBtn();
        if (!data.success) {
            alert('Error: ' + (data.error || 'Failed to initialize payment'));
            return;
        }

        showPaymentCheckoutSheet(data, btn);
    })
    .catch(err => {
        console.error('Payment initiation error:', err);
        alert('Failed to initialize payment: ' + (err.message || 'Please check your connection and try again.'));
        resetBtn();
    });
};

function showPaymentCheckoutSheet(data, targetBtn) {
    let modalEl = document.getElementById('ssgPaymentChoiceModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.id = 'ssgPaymentChoiceModal';
        modalEl.className = 'modal fade';
        modalEl.setAttribute('tabindex', '-1');
        modalEl.setAttribute('aria-hidden', 'true');
        modalEl.style.zIndex = '1060';
        document.body.appendChild(modalEl);
    }

    const formattedAmt = (data.amount / 100).toFixed(2);
    const bookingCode = data.booking_id || currentAppointmentId;

    modalEl.innerHTML = `
        <div class="modal-dialog modal-dialog-centered" style="max-width: 500px;">
            <div class="modal-content border-0 shadow-lg" style="border-radius: 24px; overflow: hidden; background: #ffffff;">
                <div class="modal-header border-0 pb-0 pt-4 px-4 d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-2">
                        <img src="/static/logo.png" alt="SkillSetGo" style="height: 38px; width: auto; object-fit: contain;">
                        <div>
                            <h5 class="modal-title fw-bold mb-0 text-dark" style="font-size: 1.15rem;">SkillSetGo Secure Checkout</h5>
                            <small class="text-muted">Booking #${bookingCode}</small>
                        </div>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                
                <div class="modal-body p-4">
                    <!-- Price Card -->
                    <div class="p-3 mb-3" style="background: linear-gradient(135deg, #f8fafc, #f1f5f9); border: 1px solid #e2e8f0; border-radius: 16px;">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="text-muted small fw-semibold text-uppercase" style="letter-spacing: 0.5px; font-size: 0.75rem;">Total Payable Amount</span>
                            <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1" style="font-size: 0.72rem;">
                                <i class="fas fa-shield-alt me-1"></i> 100% Escrow Protected
                            </span>
                        </div>
                        <div class="d-flex align-items-baseline">
                            <h2 class="fw-bold text-dark mb-0">₹${formattedAmt}</h2>
                            <small class="text-muted ms-2">(All inclusive)</small>
                        </div>
                        <p class="text-muted small mb-0 mt-2" style="font-size: 0.75rem;">
                            <i class="fas fa-lock text-primary me-1"></i> Funds held securely until you share the 6-digit Completion OTP at your doorstep.
                        </p>
                    </div>

                    <!-- Payment Navigation Tabs -->
                    <ul class="nav nav-pills nav-fill mb-3 p-1 bg-light rounded-pill border" id="pills-tab" role="tablist" style="font-size: 0.8rem;">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active rounded-pill fw-bold py-1.5" id="tab-instant-pay" data-bs-toggle="pill" data-bs-target="#pills-instant" type="button" role="tab">
                                <i class="fas fa-bolt text-warning me-1"></i> 1-Click Fast
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link rounded-pill fw-bold py-1.5" id="tab-interactive-pay" data-bs-toggle="pill" data-bs-target="#pills-interactive" type="button" role="tab">
                                <i class="fas fa-university me-1"></i> Mock Bank/Card
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link rounded-pill fw-bold py-1.5" id="tab-razorpay-pay" data-bs-toggle="pill" data-bs-target="#pills-razorpay" type="button" role="tab">
                                <i class="fas fa-external-link-alt me-1"></i> Razorpay SDK
                            </button>
                        </li>
                    </ul>

                    <div class="tab-content" id="pills-tabContent">
                        <!-- Tab 1: 1-Click Fast Escrow -->
                        <div class="tab-pane fade show active" id="pills-instant" role="tabpanel">
                            <div class="text-center py-2">
                                <p class="text-muted small mb-3">
                                    Simulate immediate escrow authorization without popups, typing card details, or handling external bank redirects.
                                </p>
                                <button id="btnInstantSandboxPay" class="btn btn-dark w-100 py-2.5 fw-bold shadow-sm d-flex justify-content-center align-items-center gap-2" style="border-radius: 12px; background: #111827; font-size: 0.95rem;">
                                    <i class="fas fa-check-circle text-success"></i> Confirm & Pay ₹${formattedAmt} in 1-Click
                                </button>
                            </div>
                        </div>

                        <!-- Tab 2: Interactive In-Modal Bank/Card Simulator -->
                        <div class="tab-pane fade" id="pills-interactive" role="tabpanel">
                            <div class="p-3 bg-light rounded-3 border mb-2" style="font-size: 0.8rem;">
                                <div class="mb-2">
                                    <label class="form-label fw-bold mb-1 text-dark">Simulate Payment Method:</label>
                                    <select class="form-select form-select-sm" id="mockMethodSelect">
                                        <option value="HDFC Bank">Netbanking: HDFC Bank</option>
                                        <option value="State Bank of India">Netbanking: State Bank of India</option>
                                        <option value="ICICI Bank">Netbanking: ICICI Bank</option>
                                        <option value="Axis Bank">Netbanking: Axis Bank</option>
                                        <option value="Visa Test Card (4111 1111 1111 1111)">Card: Visa Test Card</option>
                                        <option value="UPI (customer@okhdfcbank)">UPI: GPay / PhonePe</option>
                                    </select>
                                </div>
                                <div class="d-flex gap-2 mt-3">
                                    <button id="btnMockSuccessPay" class="btn btn-success btn-sm flex-grow-1 fw-bold py-2">
                                        <i class="fas fa-check me-1"></i> Simulate Bank Success
                                    </button>
                                    <button id="btnMockFailPay" class="btn btn-outline-danger btn-sm fw-semibold py-2">
                                        <i class="fas fa-times me-1"></i> Simulate Fail
                                    </button>
                                </div>
                            </div>
                            <small class="text-muted d-block" style="font-size: 0.72rem;">
                                * Direct in-modal simulation avoids all Chrome/Edge <code>about:blank</code> cross-origin popup blocks.
                            </small>
                        </div>

                        <!-- Tab 3: Official Razorpay SDK -->
                        <div class="tab-pane fade" id="pills-razorpay" role="tabpanel">
                            <button id="btnOpenRazorpayModal" class="btn btn-outline-primary w-100 py-2.5 fw-semibold d-flex justify-content-between align-items-center mb-2" style="border-radius: 12px; border-width: 1.5px;">
                                <span><i class="fas fa-credit-card me-2"></i> Launch Razorpay Modal</span>
                                <span class="badge bg-primary text-white">Test Mode</span>
                            </button>
                            <div class="p-2 rounded bg-light border" style="font-size: 0.75rem;">
                                <div class="fw-bold text-dark mb-1"><i class="fas fa-info-circle text-primary me-1"></i> Test Credentials:</div>
                                <div>• <strong>Card:</strong> <code>4111 1111 1111 1111</code> (Exp: 12/28, CVV: 123)</div>
                                <div>• <strong>OTP:</strong> <code>123456</code> (for Cards & Wallets)</div>
                                <div>• <em>Note: If bank popup stays blank on localhost, switch to Tab 1 or Tab 2 above.</em></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();

    document.getElementById('btnInstantSandboxPay').onclick = function() {
        if (document.activeElement) document.activeElement.blur();
        bsModal.hide();
        fallbackSimulatePayment(data, targetBtn);
    };

    document.getElementById('btnMockSuccessPay').onclick = function() {
        const method = document.getElementById('mockMethodSelect').value;
        if (document.activeElement) document.activeElement.blur();
        bsModal.hide();
        if (targetBtn) {
            targetBtn.disabled = true;
            targetBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Processing...';
        }
        verifyPayment({
            razorpay_payment_id: "pay_mock_" + Math.random().toString(36).substr(2, 9),
            razorpay_order_id: data.order_id || ("order_mock_" + Math.random().toString(36).substr(2, 9)),
            razorpay_signature: "sig_mock_" + Math.random().toString(36).substr(2, 9)
        }, targetBtn);
    };

    document.getElementById('btnMockFailPay').onclick = function() {
        alert('Simulated Payment Failure: Bank transaction was declined by user or issuer.');
    };

    document.getElementById('btnOpenRazorpayModal').onclick = function() {
        if (document.activeElement) document.activeElement.blur();
        bsModal.hide();
        launchRazorpayGateway(data, targetBtn);
    };
}

function launchRazorpayGateway(data, targetBtn) {
    const razorpayKey = data.key || 'rzp_test_TcizwraHmXHdJg';

    const cleanPrefill = {};
    if (data.prefill) {
        if (data.prefill.name) cleanPrefill.name = data.prefill.name;
        if (data.prefill.email) cleanPrefill.email = data.prefill.email;
        if (data.prefill.contact) {
            const digits = String(data.prefill.contact).replace(/\D/g, '');
            if (digits.length >= 10) {
                cleanPrefill.contact = digits.slice(-10);
            }
        }
    }

    const options = {
        key: razorpayKey,
        amount: data.amount,
        currency: data.currency || 'INR',
        name: 'SkillSetGo',
        description: `Payment for Booking #${data.booking_id || currentAppointmentId}`,
        image: window.location.origin + '/static/logo.jpeg',
        prefill: cleanPrefill,
        theme: {
            color: '#111827'
        },
        handler: function (response) {
            if (targetBtn) {
                targetBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Verifying...';
            }
            verifyPayment({
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_order_id: response.razorpay_order_id || data.order_id || '',
                razorpay_signature: response.razorpay_signature || ''
            }, targetBtn);
        },
        modal: {
            ondismiss: function() {
                if (targetBtn) {
                    targetBtn.disabled = false;
                    targetBtn.innerHTML = '<i class="fas fa-credit-card me-1"></i> Pay Now';
                }
            }
        }
    };

    if (data.order_id && typeof data.order_id === 'string' && data.order_id.startsWith('order_') && !data.order_id.startsWith('order_mock_')) {
        options.order_id = data.order_id;
    }

    function doOpen() {
        try {
            const rzp = new Razorpay(options);
            rzp.on('payment.failed', function(resp) {
                console.error('Razorpay Payment Failed:', resp.error);
                const errorReason = resp.error ? (resp.error.description || resp.error.reason || resp.error.code) : '';
                if (confirm(`Razorpay Gateway notice: ${errorReason || 'Payment could not be completed'}.\n\nWould you like to complete this payment via 1-Click Instant Test Escrow instead?`)) {
                    fallbackSimulatePayment(data, targetBtn);
                } else {
                    if (targetBtn) {
                        targetBtn.disabled = false;
                        targetBtn.innerHTML = '<i class="fas fa-credit-card me-1"></i> Pay Now';
                    }
                }
            });
            rzp.open();
        } catch (err) {
            console.error('Razorpay open error:', err);
            fallbackSimulatePayment(data, targetBtn);
        }
    }

    if (typeof Razorpay === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = doOpen;
        script.onerror = () => {
            console.warn('Could not load Razorpay CDN script. Using test simulation fallback.');
            fallbackSimulatePayment(data, targetBtn);
        };
        document.head.appendChild(script);
    } else {
        doOpen();
    }
}

function fallbackSimulatePayment(data, targetBtn) {
    if (targetBtn) {
        targetBtn.disabled = true;
        targetBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Confirming...';
    }
    verifyPayment({
        razorpay_payment_id: "pay_test_" + Math.random().toString(36).substr(2, 9),
        razorpay_order_id: data.order_id || ("order_test_" + Math.random().toString(36).substr(2, 9)),
        razorpay_signature: "sig_test_" + Math.random().toString(36).substr(2, 9)
    }, targetBtn);
}

function verifyPayment(paymentResponse, targetBtn) {
    const btn = targetBtn || document.getElementById('payNowBtn');
    fetch(`/api/appointments/${currentAppointmentId}/payment/verify/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(paymentResponse)
    })
    .then(async response => {
        let data = {};
        try { data = await response.json(); } catch(e) {}
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Payment verification failed');
        }
        return data;
    })
    .then(data => {
        alert(`Payment Verified Successfully! Your booking #${data.booking_id || currentAppointmentId} is confirmed.\n\nYour 6-digit Completion OTP is: ${data.otp || 'Available in booking details'}`);
        const modalEl = document.getElementById('appointmentModal');
        if (modalEl && modalEl.classList.contains('show')) {
            window.loadAppointmentDetails(currentAppointmentId);
        } else {
            window.location.reload();
        }
    })
    .catch(err => {
        console.error('Payment verification error:', err);
        alert('Payment Verification notice: ' + (err.message || 'An error occurred during payment verification.'));
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-credit-card me-1"></i> Pay Now';
        }
    });
}

// Utilities
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || '';
}

function getStatusColor(status) {
    switch(status) {
        case 'pending': return 'warning text-dark';
        case 'accepted': return 'primary';
        case 'completed': return 'success';
        case 'cancelled': return 'danger';
        default: return 'secondary';
    }
}