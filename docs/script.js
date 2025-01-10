// Initialize the page with articles and weights
function initializePage(articles, initialWeights, isAggregate = false) {
  // Set up global variables
  window.isAggregateView = isAggregate;
  window.initialWeights = initialWeights;
  window.currentSort = { field: 'score', direction: 'desc' };

  if (isAggregate) {
    // For aggregate view, initialize with all articles
    window.articles = articles;
    window.filteredArticles = [...articles];
    window.currentTimeFilter = 'all';
  } else {
    // For weekly view, just use the articles directly
    window.articles = articles;
    window.filteredArticles = articles;
  }

  // Set up weights UI
  setupWeightsUI(window.initialWeights);

  // Initial table render
  updateTable();

  // Set up sorting
  setupSorting();
}

// Set up the weights UI with sliders
function setupWeightsUI(weights) {
  const weightsContainer = document.getElementById('weights');
  weightsContainer.innerHTML = '';

  Object.entries(weights).forEach(([keyword, weight]) => {
    const div = document.createElement('div');
    div.className = 'weight-item';
    div.innerHTML = `
            <label for="weight-${keyword}">${keyword}</label>
            <input type="range" id="weight-${keyword}" 
                   min="0" max="10" step="0.1" value="${weight}"
                   oninput="updateWeight('${keyword}', this.value)">
            <span class="weight-value">${weight}</span>
        `;
    weightsContainer.appendChild(div);
  });
}

// Update a keyword's weight
function updateWeight(keyword, value) {
  window.initialWeights[keyword] = parseFloat(value);
  document.querySelector(`#weight-${keyword} + .weight-value`).textContent =
    value;
  updateTable();
}

// Update the article table with current weights
function updateTable() {
  const tbody = document.querySelector('#article-table tbody');
  tbody.innerHTML = '';

  // Get the current articles to display (filtered or all)
  const articlesToDisplay = window.isAggregateView
    ? window.filteredArticles
    : window.articles;

  // Calculate scores with current weights
  const scoredArticles = articlesToDisplay.map((article) => {
    let score = 0;
    const matches = article.matched_keywords.split(';').map((m) => m.trim());

    matches.forEach((match) => {
      const [keyword, locations] = match.split('(');
      if (locations) {
        const weightMultipliers = locations
          .slice(0, -1)
          .split(',')
          .map((loc) => {
            if (loc === 'kw') return 1;
            if (loc === 'title') return 0.8;
            if (loc === 'abstract') return 0.5;
            return 0;
          });
        const maxMultiplier = Math.max(...weightMultipliers);
        score += window.initialWeights[keyword] * maxMultiplier;
      }
    });

    return { ...article, currentScore: score };
  });

  // Sort articles
  const sortedArticles = sortArticles(scoredArticles);

  // Render articles
  sortedArticles.forEach((article, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${article.currentScore.toFixed(2)}</td>
            <td>
                <div class="title-toggle" onclick="toggleAbstract(${index})">
                    ${
                      article.doi
                        ? `<a href="https://doi.org/${article.doi}" target="_blank">${article.title}</a>`
                        : article.title
                    }
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="abstract" id="abstract-${index}">${
      article.abstract
    }</div>
            </td>
            <td>
                ${article.authors}
                <br><br>
                <span class="affiliation">${
                  article.first_author_affiliation
                }</span>
            </td>
            <td>${article.journal}</td>
            <td>${article.pub_date}</td>
            <td>${article.api_keywords}</td>
            <td>${article.matched_keywords}</td>
        `;
    tbody.appendChild(tr);
  });
}

// Toggle abstract visibility
function toggleAbstract(index) {
  const abstract = document.getElementById(`abstract-${index}`);
  const toggleIcon =
    abstract.previousElementSibling.querySelector('.toggle-icon');
  abstract.classList.toggle('expanded');
  toggleIcon.textContent = abstract.classList.contains('expanded') ? '▲' : '▼';
}

// Sort articles based on current sort field and direction
function sortArticles(articles) {
  return [...articles].sort((a, b) => {
    let aVal =
      window.currentSort.field === 'score'
        ? a.currentScore
        : a[window.currentSort.field];
    let bVal =
      window.currentSort.field === 'score'
        ? b.currentScore
        : b[window.currentSort.field];

    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();

    if (aVal < bVal) return window.currentSort.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return window.currentSort.direction === 'asc' ? 1 : -1;
    return 0;
  });
}

// Set up sorting functionality
function setupSorting() {
  document.querySelectorAll('th.sortable').forEach((th) => {
    th.addEventListener('click', () => {
      const field = th.dataset.sort;
      if (window.currentSort.field === field) {
        window.currentSort.direction =
          window.currentSort.direction === 'asc' ? 'desc' : 'asc';
      } else {
        window.currentSort.field = field;
        window.currentSort.direction = 'desc';
      }
      updateTable();
    });
  });
}

// Time filtering functions for aggregate view
function setTimeFilter(filter) {
  if (!window.isAggregateView) return; // Only run in aggregate view

  window.currentTimeFilter = filter;
  document.querySelectorAll('.filter-buttons button').forEach((btn) => {
    btn.classList.remove('active');
  });
  document
    .querySelector(`button[onclick="setTimeFilter('${filter}')"]`)
    .classList.add('active');

  const now = new Date();
  let startDate = null;
  let endDate = null;

  switch (filter) {
    case 'thisYear':
      startDate = new Date(now.getFullYear(), 0, 1); // January 1st of current year
      endDate = new Date(now.getFullYear(), 11, 31); // December 31st of current year
      break;
    case 'lastYear':
      startDate = new Date(now.getFullYear() - 1, 0, 1); // January 1st of last year
      endDate = new Date(now.getFullYear() - 1, 11, 31); // December 31st of last year
      break;
    case 'thisMonth':
      startDate = new Date(now.getFullYear(), now.getMonth(), 1); // 1st of current month
      endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0); // Last day of current month
      break;
    case 'lastMonth':
      startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1); // 1st of last month
      endDate = new Date(now.getFullYear(), now.getMonth(), 0); // Last day of last month
      break;
    case 'week':
      startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // Last 7 days
      endDate = now;
      break;
    case 'all':
      startDate = null;
      endDate = null;
      break;
  }

  if (startDate && endDate) {
    document.getElementById('startDate').value = startDate
      .toISOString()
      .split('T')[0];
    document.getElementById('endDate').value = endDate
      .toISOString()
      .split('T')[0];
  } else {
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
  }

  updateDateFilter();
}

function updateDateFilter() {
  if (!window.isAggregateView) return; // Only run in aggregate view

  const startDate = document.getElementById('startDate').value;
  const endDate = document.getElementById('endDate').value;

  if (startDate && endDate) {
    const startDateTime = new Date(startDate);
    const endDateTime = new Date(endDate);
    // Set end time to end of day
    endDateTime.setHours(23, 59, 59, 999);

    window.filteredArticles = window.articles.filter((article) => {
      const pubDate = new Date(article.pub_date);
      return pubDate >= startDateTime && pubDate <= endDateTime;
    });

    // Format date range for display
    const startDisplay = startDateTime.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    const endDisplay = endDateTime.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    document.getElementById(
      'articleCount'
    ).textContent = `Showing ${window.filteredArticles.length} articles from ${startDisplay} to ${endDisplay}`;
  } else {
    window.filteredArticles = [...window.articles];
    document.getElementById(
      'articleCount'
    ).textContent = `Showing all ${window.filteredArticles.length} articles`;
  }

  updateTable();
}
