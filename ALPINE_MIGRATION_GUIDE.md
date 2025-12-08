# Alpine.js Migration Guide

**Goal**: Add Alpine.js to improve state management and reduce DOM manipulation code.

**Effort**: 1-2 hours  
**Risk**: Very low (no build step, no breaking changes)

---

## What is Alpine.js?

Alpine.js is a lightweight JavaScript framework (15kb) that adds reactivity to your HTML. Think of it as "Tailwind for JavaScript" - you add directives directly to your HTML.

**Key Benefits**:
- ✅ No build step (works via CDN)
- ✅ Works with server-rendered HTML
- ✅ Reduces JavaScript code by 50%
- ✅ More declarative and maintainable
- ✅ Perfect for modals, dropdowns, toggles

---

## Step 1: Add Alpine.js to Base Template

**File**: `app/templates/base.html`

Add this line before the closing `</body>` tag:

```html
<!-- Add Alpine.js (before closing body tag) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
```

**Full context**:
```html
    {% block extra_js %}{% endblock %}
    
    <!-- Add Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
</body>
</html>
```

---

## Step 2: Refactor Booking Modal

### Current Implementation (booking.js)

**Problems**:
- Manual DOM manipulation
- Global functions polluting window scope
- Hard to track modal state

### Alpine.js Implementation

**File**: `app/templates/dashboard.html`

**Before**:
```html
<div id="booking-modal" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50">
    <!-- Modal content -->
</div>

<script>
function openBookingModal(courtId, time) {
    document.getElementById('booking-modal').classList.remove('hidden');
}
</script>
```

**After**:
```html
<div x-data="bookingModal()">
    <!-- Modal -->
    <div x-show="open" 
         x-cloak
         @keydown.escape.window="close()"
         class="fixed inset-0 bg-gray-600 bg-opacity-50">
        
        <div class="bg-white rounded-lg p-6 max-w-md mx-auto mt-20">
            <h2 class="text-xl font-bold mb-4">Platz buchen</h2>
            
            <form @submit.prevent="submitBooking()">
                <div class="mb-4">
                    <label class="block mb-2">Platz</label>
                    <input type="text" x-model="courtId" readonly class="w-full p-2 border rounded">
                </div>
                
                <div class="mb-4">
                    <label class="block mb-2">Uhrzeit</label>
                    <input type="text" x-model="time" readonly class="w-full p-2 border rounded">
                </div>
                
                <div class="mb-4">
                    <label class="block mb-2">Gebucht für</label>
                    <select x-model="bookedForId" class="w-full p-2 border rounded">
                        <option value="">Wählen Sie ein Mitglied</option>
                        <!-- Options populated by server -->
                    </select>
                </div>
                
                <div class="flex gap-2">
                    <button type="submit" 
                            :disabled="loading"
                            class="bg-green-600 text-white px-4 py-2 rounded">
                        <span x-show="!loading">Buchung bestätigen</span>
                        <span x-show="loading">Wird gebucht...</span>
                    </button>
                    <button type="button" 
                            @click="close()"
                            class="bg-gray-300 px-4 py-2 rounded">
                        Abbrechen
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function bookingModal() {
    return {
        open: false,
        loading: false,
        courtId: null,
        time: null,
        date: null,
        bookedForId: '',
        
        openModal(courtId, time, date) {
            this.courtId = courtId;
            this.time = time;
            this.date = date;
            this.open = true;
        },
        
        close() {
            this.open = false;
            this.loading = false;
            this.bookedForId = '';
        },
        
        async submitBooking() {
            if (!this.bookedForId) {
                showToast('Bitte wählen Sie ein Mitglied', 'error');
                return;
            }
            
            this.loading = true;
            
            try {
                const response = await fetch('/reservations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        court_id: this.courtId,
                        date: this.date,
                        start_time: this.time,
                        booked_for_id: this.bookedForId
                    })
                });
                
                if (response.ok) {
                    showToast('Buchung erfolgreich erstellt');
                    this.close();
                    // Reload grid
                    window.location.reload();
                } else {
                    const data = await response.json();
                    showToast(data.error || 'Fehler beim Buchen', 'error');
                }
            } catch (error) {
                showToast('Netzwerkfehler', 'error');
            } finally {
                this.loading = false;
            }
        }
    }
}
</script>
```

**Key Alpine.js Directives**:
- `x-data`: Defines component state
- `x-show`: Toggles visibility (like v-show in Vue)
- `x-model`: Two-way data binding
- `@click`: Event listener (shorthand for x-on:click)
- `@submit.prevent`: Prevent form submission
- `:disabled`: Bind attribute (shorthand for x-bind:disabled)
- `x-cloak`: Hide element until Alpine loads

---

## Step 3: Refactor Court Grid Cells

### Make Grid Cells Interactive with Alpine

**File**: `app/templates/dashboard.html`

**Before**:
```html
<td onclick="openBookingModal({{ court.number }}, '{{ time }}')">
    Available
</td>
```

**After**:
```html
<td @click="$dispatch('open-booking', { 
        courtId: {{ court.number }}, 
        time: '{{ time }}',
        date: currentDate 
    })"
    class="cursor-pointer hover:bg-green-200">
    Available
</td>
```

**In the booking modal component**:
```html
<div x-data="bookingModal()" 
     @open-booking.window="openModal($event.detail.courtId, $event.detail.time, $event.detail.date)">
    <!-- Modal content -->
</div>
```

**Benefits**:
- No global functions
- Event-driven communication
- Cleaner separation of concerns

---

## Step 4: Refactor Member Search

### Current Implementation

**Problems**:
- Manual DOM updates
- Debouncing logic in JavaScript
- State scattered across functions

### Alpine.js Implementation

**File**: `app/templates/favourites.html`

```html
<div x-data="memberSearch()">
    <!-- Search Input -->
    <div class="mb-4">
        <input 
            type="text"
            x-model="query"
            @input.debounce.300ms="search()"
            placeholder="Mitglied suchen..."
            class="w-full p-2 border rounded">
    </div>
    
    <!-- Loading State -->
    <div x-show="loading" class="text-gray-500">
        Suche läuft...
    </div>
    
    <!-- Results -->
    <div x-show="!loading && results.length > 0" class="space-y-2">
        <template x-for="member in results" :key="member.id">
            <div class="flex justify-between items-center p-3 bg-white rounded shadow">
                <div>
                    <div class="font-semibold" x-text="member.firstname + ' ' + member.lastname"></div>
                    <div class="text-sm text-gray-600" x-text="member.email"></div>
                </div>
                <button 
                    @click="addToFavourites(member.id)"
                    :disabled="adding === member.id"
                    class="bg-green-600 text-white px-3 py-1 rounded text-sm">
                    <span x-show="adding !== member.id">Hinzufügen</span>
                    <span x-show="adding === member.id">...</span>
                </button>
            </div>
        </template>
    </div>
    
    <!-- Empty State -->
    <div x-show="!loading && query && results.length === 0" class="text-gray-500">
        Keine Mitglieder gefunden
    </div>
</div>

<script>
function memberSearch() {
    return {
        query: '',
        results: [],
        loading: false,
        adding: null,
        
        async search() {
            if (!this.query) {
                this.results = [];
                return;
            }
            
            this.loading = true;
            
            try {
                const response = await fetch(`/members/search?q=${encodeURIComponent(this.query)}`);
                const data = await response.json();
                this.results = data.results || [];
            } catch (error) {
                console.error('Search error:', error);
                this.results = [];
            } finally {
                this.loading = false;
            }
        },
        
        async addToFavourites(memberId) {
            this.adding = memberId;
            
            try {
                const response = await fetch(`/members/${memberId}/favourites`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    showToast('Favorit hinzugefügt');
                    // Remove from results
                    this.results = this.results.filter(m => m.id !== memberId);
                } else {
                    showToast('Fehler beim Hinzufügen', 'error');
                }
            } catch (error) {
                showToast('Netzwerkfehler', 'error');
            } finally {
                this.adding = null;
            }
        }
    }
}
</script>
```

**Key Features**:
- `@input.debounce.300ms`: Built-in debouncing!
- `x-for`: Loop through results
- `x-text`: Set text content
- `:key`: Unique identifier for list items
- Reactive state updates

---

## Step 5: Refactor Reservation Cancellation

### Add Confirmation Dialog with Alpine

**File**: `app/templates/reservations.html`

```html
<div x-data="{ 
    confirmingId: null,
    cancelling: null 
}">
    <template x-for="reservation in reservations" :key="reservation.id">
        <div class="bg-white p-4 rounded shadow">
            <div class="flex justify-between items-center">
                <div>
                    <div class="font-semibold">
                        Platz <span x-text="reservation.court_number"></span>
                    </div>
                    <div class="text-sm text-gray-600">
                        <span x-text="reservation.date"></span> um 
                        <span x-text="reservation.start_time"></span>
                    </div>
                </div>
                
                <button 
                    @click="confirmingId = reservation.id"
                    class="bg-red-600 text-white px-3 py-1 rounded text-sm">
                    Stornieren
                </button>
            </div>
            
            <!-- Confirmation Dialog -->
            <div x-show="confirmingId === reservation.id" 
                 x-cloak
                 class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p class="text-sm mb-2">Buchung wirklich stornieren?</p>
                <div class="flex gap-2">
                    <button 
                        @click="cancelReservation(reservation.id)"
                        :disabled="cancelling === reservation.id"
                        class="bg-red-600 text-white px-3 py-1 rounded text-sm">
                        <span x-show="cancelling !== reservation.id">Ja, stornieren</span>
                        <span x-show="cancelling === reservation.id">...</span>
                    </button>
                    <button 
                        @click="confirmingId = null"
                        class="bg-gray-300 px-3 py-1 rounded text-sm">
                        Abbrechen
                    </button>
                </div>
            </div>
        </div>
    </template>
</div>

<script>
async function cancelReservation(id) {
    this.cancelling = id;
    
    try {
        const response = await fetch(`/reservations/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Buchung storniert');
            // Remove from list
            this.reservations = this.reservations.filter(r => r.id !== id);
        } else {
            showToast('Fehler beim Stornieren', 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler', 'error');
    } finally {
        this.cancelling = null;
        this.confirmingId = null;
    }
}
</script>
```

---

## Step 6: Add Alpine.js Styles

Add this to your CSS to hide elements until Alpine loads:

**File**: `app/static/css/styles.css` or in `base.html`:

```html
<style>
    [x-cloak] { 
        display: none !important; 
    }
</style>
```

---

## Step 7: Clean Up JavaScript Files

After migrating to Alpine, you can simplify or remove:

### booking.js
- Remove `openBookingModal()`, `closeBookingModal()`
- Keep only the fetch logic (or move to Alpine component)

### member-search.js
- Remove debouncing logic
- Remove DOM manipulation
- Keep only fetch logic (or move to Alpine component)

### app.js
- Remove global function assignments
- Keep only initialization logic

---

## Migration Checklist

- [ ] Add Alpine.js CDN to base.html
- [ ] Add `[x-cloak]` CSS
- [ ] Refactor booking modal
- [ ] Refactor court grid interactions
- [ ] Refactor member search
- [ ] Refactor reservation cancellation
- [ ] Test all functionality
- [ ] Remove unused JavaScript code
- [ ] Update documentation

---

## Testing After Migration

1. **Booking Modal**
   - [ ] Opens when clicking available slot
   - [ ] Closes on cancel button
   - [ ] Closes on ESC key
   - [ ] Shows loading state during submission
   - [ ] Shows error messages

2. **Member Search**
   - [ ] Debounces input (wait 300ms)
   - [ ] Shows loading state
   - [ ] Displays results
   - [ ] Shows empty state
   - [ ] Adds to favourites

3. **Reservation Cancellation**
   - [ ] Shows confirmation dialog
   - [ ] Cancels on confirm
   - [ ] Closes on cancel
   - [ ] Shows loading state
   - [ ] Removes from list

---

## Benefits After Migration

✅ **Less Code**: ~50% reduction in JavaScript  
✅ **More Declarative**: State and UI in one place  
✅ **Easier to Maintain**: No manual DOM manipulation  
✅ **Better UX**: Built-in loading states and transitions  
✅ **No Build Step**: Still works via CDN  
✅ **Type Safety**: Can add TypeScript later if needed  

---

## Common Alpine.js Patterns

### Toggle Visibility
```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Content</div>
</div>
```

### Form with Validation
```html
<div x-data="{ 
    email: '', 
    isValid() { return this.email.includes('@'); } 
}">
    <input x-model="email" type="email">
    <span x-show="!isValid()" class="text-red-600">Invalid email</span>
</div>
```

### Loading State
```html
<div x-data="{ loading: false }">
    <button @click="loading = true; await doSomething(); loading = false">
        <span x-show="!loading">Submit</span>
        <span x-show="loading">Loading...</span>
    </button>
</div>
```

### List with Actions
```html
<div x-data="{ items: [], removing: null }">
    <template x-for="item in items" :key="item.id">
        <div>
            <span x-text="item.name"></span>
            <button @click="removing = item.id; await remove(item.id); removing = null">
                <span x-show="removing !== item.id">Delete</span>
                <span x-show="removing === item.id">...</span>
            </button>
        </div>
    </template>
</div>
```

---

## Resources

- **Alpine.js Docs**: https://alpinejs.dev/
- **Alpine.js Cheatsheet**: https://alpinejs.dev/directives
- **Examples**: https://alpinejs.dev/examples

---

## Need Help?

If you encounter issues:
1. Check browser console for errors
2. Verify Alpine.js loaded (check Network tab)
3. Check `x-cloak` CSS is present
4. Verify `defer` attribute on script tag

---

**Ready to start?** Let's begin with Step 1!
