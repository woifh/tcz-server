/**
 * Calendar View Component
 * Handles calendar display and navigation for blocks
 */

import { blocksAPI } from '../core/admin-api.js';
import { showToast, dateUtils } from '../core/admin-utils.js';
import { stateManager } from '../core/admin-state.js';
import { getToday, toBerlinDateString } from '../../../utils/date-utils.js';

export class CalendarView {
    constructor() {
        this.currentDate = new Date();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Calendar navigation
        const prevBtn = document.getElementById('calendar-prev-btn');
        const nextBtn = document.getElementById('calendar-next-btn');
        const todayBtn = document.getElementById('calendar-today-btn');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.navigateMonth(-1));
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.navigateMonth(1));
        }

        if (todayBtn) {
            todayBtn.addEventListener('click', () => this.goToToday());
        }

        // View toggle buttons
        const monthViewBtn = document.getElementById('calendar-month-view');
        const weekViewBtn = document.getElementById('calendar-week-view');

        if (monthViewBtn) {
            monthViewBtn.addEventListener('click', () => this.setView('month'));
        }

        if (weekViewBtn) {
            weekViewBtn.addEventListener('click', () => this.setView('week'));
        }
    }

    async initialize() {
        stateManager.setCalendarDate(this.currentDate);
        await this.loadCalendarData();
        this.renderCalendar();
    }

    async loadCalendarData() {
        try {
            const startDate = this.getCalendarStartDate();
            const endDate = this.getCalendarEndDate();

            const result = await blocksAPI.load({
                date_range_start: startDate,
                date_range_end: endDate,
            });

            if (result.success) {
                stateManager.setCalendarBlocks(result.blocks);
            } else {
                showToast(result.error || 'Fehler beim Laden der Kalenderdaten', 'error');
            }
        } catch (error) {
            console.error('Error loading calendar data:', error);
            showToast('Fehler beim Laden der Kalenderdaten', 'error');
        }
    }

    getCalendarStartDate() {
        const date = new Date(this.currentDate);
        date.setDate(1); // First day of month

        // Go back to the first Monday of the calendar view
        const dayOfWeek = date.getDay();
        const daysToSubtract = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // Monday = 0
        date.setDate(date.getDate() - daysToSubtract);

        return toBerlinDateString(date);
    }

    getCalendarEndDate() {
        const date = new Date(this.currentDate);
        date.setMonth(date.getMonth() + 1, 0); // Last day of month

        // Go forward to the last Sunday of the calendar view
        const dayOfWeek = date.getDay();
        const daysToAdd = dayOfWeek === 0 ? 0 : 7 - dayOfWeek;
        date.setDate(date.getDate() + daysToAdd);

        return toBerlinDateString(date);
    }

    renderCalendar() {
        const container = document.getElementById('calendar-container');
        if (!container) return;

        const blocks = stateManager.getCalendarBlocks();
        const blocksByDate = this.groupBlocksByDate(blocks);

        // Update calendar header
        this.updateCalendarHeader();

        // Render calendar grid
        const calendarHtml = this.generateCalendarHtml(blocksByDate);
        container.innerHTML = calendarHtml;

        // Add event listeners to calendar cells
        this.setupCalendarCellListeners();
    }

    updateCalendarHeader() {
        const headerElement = document.getElementById('calendar-header');
        if (headerElement) {
            const monthNames = [
                'Januar',
                'Februar',
                'März',
                'April',
                'Mai',
                'Juni',
                'Juli',
                'August',
                'September',
                'Oktober',
                'November',
                'Dezember',
            ];

            const month = monthNames[this.currentDate.getMonth()];
            const year = this.currentDate.getFullYear();

            headerElement.textContent = `${month} ${year}`;
        }
    }

    generateCalendarHtml(blocksByDate) {
        const startDate = new Date(this.getCalendarStartDate());
        const endDate = new Date(this.getCalendarEndDate());
        const today = getToday();
        const currentMonth = this.currentDate.getMonth();

        let html = `
            <div class="calendar-grid">
                <div class="calendar-header-row">
                    <div class="calendar-day-header">Mo</div>
                    <div class="calendar-day-header">Di</div>
                    <div class="calendar-day-header">Mi</div>
                    <div class="calendar-day-header">Do</div>
                    <div class="calendar-day-header">Fr</div>
                    <div class="calendar-day-header">Sa</div>
                    <div class="calendar-day-header">So</div>
                </div>
        `;

        const current = new Date(startDate);

        while (current <= endDate) {
            const dateStr = toBerlinDateString(current);
            const dayBlocks = blocksByDate[dateStr] || [];
            const isToday = dateStr === today;
            const isCurrentMonth = current.getMonth() === currentMonth;
            const isWeekend = current.getDay() === 0 || current.getDay() === 6;

            let cellClass = 'calendar-day';
            if (isToday) cellClass += ' today';
            if (!isCurrentMonth) cellClass += ' other-month';
            if (isWeekend) cellClass += ' weekend';
            if (dayBlocks.length > 0) cellClass += ' has-blocks';

            html += `
                <div class="${cellClass}" data-date="${dateStr}">
                    <div class="calendar-day-number">${current.getDate()}</div>
                    <div class="calendar-day-blocks">
                        ${this.renderDayBlocks(dayBlocks)}
                    </div>
                </div>
            `;

            current.setDate(current.getDate() + 1);
        }

        html += '</div>';
        return html;
    }

    renderDayBlocks(blocks) {
        if (blocks.length === 0) return '';

        // Group blocks by batch_id
        const batches = {};
        blocks.forEach((block) => {
            if (!batches[block.batch_id]) {
                batches[block.batch_id] = [];
            }
            batches[block.batch_id].push(block);
        });

        let html = '';
        let displayCount = 0;
        const maxDisplay = 3;

        Object.keys(batches).forEach((batchId) => {
            if (displayCount >= maxDisplay) return;

            const batchBlocks = batches[batchId];
            const firstBlock = batchBlocks[0];
            const courtCount = batchBlocks.length;

            const blockClass = this.getBlockClass(firstBlock);
            const timeText = `${dateUtils.formatTime(firstBlock.start_time)}-${dateUtils.formatTime(firstBlock.end_time)}`;
            const courtText =
                courtCount === 1 ? `Platz ${firstBlock.court_name}` : `${courtCount} Plätze`;

            html += `
                <div class="calendar-block ${blockClass}" 
                     data-batch-id="${batchId}"
                     title="${firstBlock.reason_name} - ${timeText} - ${courtText}">
                    <div class="calendar-block-time">${timeText}</div>
                    <div class="calendar-block-courts">${courtText}</div>
                    <div class="calendar-block-reason">${firstBlock.reason_name}</div>
                </div>
            `;

            displayCount++;
        });

        // Show "more" indicator if there are additional blocks
        const remainingBatches = Object.keys(batches).length - displayCount;
        if (remainingBatches > 0) {
            html += `
                <div class="calendar-block-more">
                    +${remainingBatches} weitere
                </div>
            `;
        }

        return html;
    }

    getBlockClass(block) {
        // You can customize this based on block properties
        const now = new Date();
        const blockDate = new Date(block.date);

        if (blockDate < now) {
            return 'past-block';
        } else if (blockDate.toDateString() === now.toDateString()) {
            return 'today-block';
        } else {
            return 'future-block';
        }
    }

    setupCalendarCellListeners() {
        // Day cell clicks
        const dayCells = document.querySelectorAll('.calendar-day');
        dayCells.forEach((cell) => {
            cell.addEventListener('click', (e) => {
                if (!e.target.closest('.calendar-block')) {
                    const date = cell.dataset.date;
                    this.handleDayClick(date);
                }
            });
        });

        // Block clicks
        const blockElements = document.querySelectorAll('.calendar-block');
        blockElements.forEach((block) => {
            block.addEventListener('click', (e) => {
                e.stopPropagation();
                const batchId = block.dataset.batchId;
                this.handleBlockClick(batchId);
            });
        });
    }

    handleDayClick(date) {
        // Open create block modal with pre-filled date
        if (window.blockForm) {
            const dateInput = document.getElementById('multi-date');
            if (dateInput) {
                dateInput.value = date;
            }

            // Show the create block modal
            const modal = document.getElementById('multi-court-modal');
            if (modal && window.bootstrap) {
                const bsModal = new window.bootstrap.Modal(modal);
                bsModal.show();
            }
        }
    }

    handleBlockClick(batchId) {
        // Navigate to block edit page or show block details
        if (window.location.pathname.includes('/admin/court-blocking')) {
            window.location.href = `/admin/court-blocking/${batchId}`;
        } else {
            // Show block details modal
            this.showBlockDetailsModal(batchId);
        }
    }

    async showBlockDetailsModal(batchId) {
        try {
            const blocks = stateManager.getCalendarBlocks();
            const batchBlocks = blocks.filter((block) => block.batch_id === batchId);

            if (batchBlocks.length === 0) {
                showToast('Sperrungsdetails nicht gefunden', 'error');
                return;
            }

            // Create and show details modal
            this.createBlockDetailsModal(batchBlocks);
        } catch (error) {
            console.error('Error showing block details:', error);
            showToast('Fehler beim Laden der Sperrungsdetails', 'error');
        }
    }

    createBlockDetailsModal(blocks) {
        const existingModal = document.getElementById('block-details-modal');
        if (existingModal) {
            existingModal.remove();
        }

        const firstBlock = blocks[0];
        const courtNames = blocks.map((b) => b.court_name).join(', ');

        const modalHtml = `
            <div class="modal fade" id="block-details-modal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Sperrungsdetails</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-sm-4"><strong>Datum:</strong></div>
                                <div class="col-sm-8">${dateUtils.formatDate(firstBlock.date)}</div>
                            </div>
                            <div class="row">
                                <div class="col-sm-4"><strong>Zeit:</strong></div>
                                <div class="col-sm-8">${dateUtils.formatTime(firstBlock.start_time)} - ${dateUtils.formatTime(firstBlock.end_time)}</div>
                            </div>
                            <div class="row">
                                <div class="col-sm-4"><strong>Plätze:</strong></div>
                                <div class="col-sm-8">${courtNames}</div>
                            </div>
                            <div class="row">
                                <div class="col-sm-4"><strong>Grund:</strong></div>
                                <div class="col-sm-8">${firstBlock.reason_name}</div>
                            </div>
                            ${
                                firstBlock.details
                                    ? `
                            <div class="row">
                                <div class="col-sm-4"><strong>Details:</strong></div>
                                <div class="col-sm-8">${firstBlock.details}</div>
                            </div>
                            `
                                    : ''
                            }
                            ${
                                firstBlock.description
                                    ? `
                            <div class="row">
                                <div class="col-sm-4"><strong>Beschreibung:</strong></div>
                                <div class="col-sm-8">${firstBlock.description}</div>
                            </div>
                            `
                                    : ''
                            }
                            <div class="row">
                                <div class="col-sm-4"><strong>Batch ID:</strong></div>
                                <div class="col-sm-8">${firstBlock.batch_id}</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Schließen</button>
                            <button type="button" class="btn btn-primary" onclick="window.location.href='/admin/court-blocking/${firstBlock.batch_id}'">
                                Bearbeiten
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = document.getElementById('block-details-modal');
        if (modal && window.bootstrap) {
            const bsModal = new window.bootstrap.Modal(modal);
            bsModal.show();

            // Remove modal from DOM when hidden
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
            });
        }
    }

    groupBlocksByDate(blocks) {
        const grouped = {};

        blocks.forEach((block) => {
            const date = block.date;
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(block);
        });

        return grouped;
    }

    async navigateMonth(direction) {
        this.currentDate.setMonth(this.currentDate.getMonth() + direction);
        stateManager.setCalendarDate(this.currentDate);

        await this.loadCalendarData();
        this.renderCalendar();
    }

    async goToToday() {
        this.currentDate = new Date();
        stateManager.setCalendarDate(this.currentDate);

        await this.loadCalendarData();
        this.renderCalendar();
    }

    setView(viewType) {
        // Update active view button
        const monthBtn = document.getElementById('calendar-month-view');
        const weekBtn = document.getElementById('calendar-week-view');

        if (monthBtn && weekBtn) {
            monthBtn.classList.toggle('active', viewType === 'month');
            weekBtn.classList.toggle('active', viewType === 'week');
        }

        // TODO: Implement week view if needed
        if (viewType === 'week') {
            showToast('Wochenansicht noch nicht implementiert', 'info');
        }
    }
}

// Export singleton instance
export const calendarView = new CalendarView();
