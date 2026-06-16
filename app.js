(function () {
  "use strict";

  // ====== 从 HTML 中读取内置数据（双击文件也能用） ======
  var INLINE_DATA = (function () {
    try {
      var el = document.getElementById("initialData");
      return JSON.parse(el.textContent);
    } catch (e) {
      return { date: "", updatedAt: "", domestic: [], international: [] };
    }
  })();

  var flightsData = { domestic: [], international: [] };
  var currentTab = "domestic";
  var currentDate = "";
  var currentFlight = null;

  var DOM = {};

  // ====== 航司配色 ======

  var AIRLINE_COLORS = {
    "山东航空": "#1a5276", "中国国航": "#b52a2a", "东方航空": "#1a73e8",
    "南方航空": "#6a1b9a", "海南航空": "#c0392b", "春秋航空": "#2e7d32",
    "四川航空": "#00838f", "厦门航空": "#0d47a1", "深圳航空": "#e65100",
    "西藏航空": "#4a148c", "瑞丽航空": "#ad1457", "北部湾航空": "#00897b",
    "成都航空": "#ef6c00", "东海航空": "#1565c0", "青岛航空": "#00695c",
    "华夏航空": "#7b1fa2", "首都航空": "#b71c1c", "桂林航空": "#33691e",
    "祥鹏航空": "#880e4f", "西部航空": "#e65100", "金鹏航空": "#00838f",
    "天津航空": "#37474f", "上海航空": "#1a237e", "昆明航空": "#4e342e",
    "吉祥航空": "#bf360c", "奥凯航空": "#283593", "澳门航空": "#004d40",
  };

  function getAirlineColor(name) {
    return AIRLINE_COLORS[name] || "#666";
  }

  // ====== 工具 ======

  function formatDate(str) {
    if (!str) {
      var d = new Date();
      return (d.getMonth() + 1) + "月" + d.getDate() + "日";
    }
    var p = str.split("-");
    if (p.length === 3) return parseInt(p[1]) + "月" + parseInt(p[2]) + "日";
    return str;
  }

  function formatDateShort(str) {
    if (!str) return "--";
    var p = str.split("-");
    if (p.length === 3) return p[1] + "-" + p[2];
    return str;
  }

  function priceTag(p) { return p <= 300 ? "超低价" : p <= 400 ? "低价" : ""; }
  function isHot(p) { return p <= 300; }

  function getCurrentFlights() {
    var all = flightsData[currentTab] || [];
    return currentDate ? all.filter(function (f) { return f.date === currentDate; }) : all;
  }

  function getUniqueDates(flights) {
    var map = {};
    for (var i = 0; i < flights.length; i++) {
      if (flights[i].date) map[flights[i].date] = true;
    }
    return Object.keys(map).sort();
  }

  // ====== 渲染日期筛选 ======

  function renderDateFilter() {
    var dates = getUniqueDates(flightsData[currentTab] || []);
    DOM.dateList.innerHTML = "";
    document.getElementById("dateAllBtn").className = "date-btn active";

    for (var i = 0; i < dates.length; i++) {
      var btn = document.createElement("button");
      btn.className = "date-btn" + (dates[i] === currentDate ? " active" : "");
      btn.textContent = formatDateShort(dates[i]);
      btn.dataset.date = dates[i];
      btn.addEventListener("click", function () {
        currentDate = this.dataset.date;
        renderDateFilter();
        renderFlights(getCurrentFlights());
      });
      DOM.dateList.appendChild(btn);
    }
  }

  // ====== 渲染主列表 ======

  function renderFlights(flights) {
    if (!flights || flights.length === 0) {
      DOM.flightList.innerHTML = '<div class="empty">暂无符合条件的航班</div>';
      DOM.summaryBar.style.display = "none";
      return;
    }

    DOM.summaryBar.style.display = "block";

    var sorted = flights.slice().sort(function (a, b) { return a.price - b.price; });
    DOM.totalCount.textContent = sorted.length;
    DOM.minPrice.textContent = "¥" + sorted[0].price;

    var html = "";
    for (var i = 0; i < sorted.length; i++) {
      var f = sorted[i];
      var tag = priceTag(f.price);
      var hot = isHot(f.price);
      var country = f.countryName || "";
      var ctryBadge = (country && country !== "中国") ? '<span class="country-badge">' + country + "</span>" : "";
      var alColor = getAirlineColor(f.airline);
      var alBadge = '<span class="airline-tag" style="background:' + alColor + '">' + f.airline + "</span>";
      var hasRet = f.returns && f.returns.length > 0;

      var p = f.platforms || {};
      var plats = "";
      if (p.qunar)  plats += '<a class="platform-link qunar" href="' + p.qunar + '" target="_blank">去哪儿</a>';
      if (p.ctrip)  plats += '<a class="platform-link ctrip" href="' + p.ctrip + '" target="_blank">携程</a>';
      if (p.fliggy) plats += '<a class="platform-link fliggy" href="' + p.fliggy + '" target="_blank">飞猪</a>';

      html +=
        '<div class="flight-card" data-idx="' + i + '">' +
          '<div class="route">&#9992; ' + f.destination + ctryBadge + '</div>' +
          '<div class="info">' + alBadge + '<span class="sep-dot"> &middot; </span>' + (f.flightNo || "--") + '</div>' +
          '<div class="date">' + formatDate(f.date) + '</div>' +
          '<div class="price' + (hot ? " hot" : "") + '">' +
            '<span class="currency">¥</span>' + f.price +
            (tag ? '<span class="tag">' + tag + "</span>" : "") +
          "</div>" +
          (plats ? '<div class="platforms">' + plats + "</div>" : "") +
          (hasRet ? '<div class="return-hint">&#x21C5; 查看返程</div>' : "") +
        "</div>";
    }

    DOM.flightList.innerHTML = html;
  }

  function switchTab(tab) {
    currentTab = tab;
    currentDate = "";
    for (var i = 0; i < DOM.tabs.length; i++) {
      DOM.tabs[i].classList.toggle("active", DOM.tabs[i].dataset.tab === tab);
    }
    renderDateFilter();
    renderFlights(getCurrentFlights());
  }

  function updateMeta(data) {
    DOM.dataDate.textContent = data.date || "--";
    DOM.updateTime.textContent = data.updatedAt || "--";
    DOM.domesticCount.textContent = (data.domestic || []).length;
    DOM.internationalCount.textContent = (data.international || []).length;
  }

  // ====== 返程弹窗 ======

  function renderReturns(returns) {
    if (!returns || returns.length === 0) return '<div class="return-empty">暂无返程数据</div>';
    var s = returns.slice().sort(function (a, b) { return a.price - b.price; });
    var h = "";
    for (var i = 0; i < s.length; i++) {
      var r = s[i];
      h +=
        '<div class="return-item">' +
          '<div class="return-info">' +
            '<div class="return-route-label">' + currentFlight.destination + ' &#9992; 济南</div>' +
            '<div class="return-meta">' + r.airline + '<span class="sep-dot"> &middot; </span>' + (r.flightNo || "--") +
            '<span class="sep-dot"> &middot; </span>' + formatDate(r.date) + "</div>" +
          "</div>" +
          '<div class="return-price"><span class="currency">¥</span>' + r.price + "</div>" +
        "</div>";
    }
    return h;
  }

  function openModal(flight) {
    currentFlight = flight;
    DOM.modalDest.textContent = flight.destination;
    DOM.modalSub.innerHTML = flight.airline + " &middot; " + (flight.flightNo || "--") + " &middot; " + formatDate(flight.date) + " &middot; ¥" + flight.price;
    DOM.modalReturns.innerHTML = '<div class="loading">加载中...</div>';
    DOM.modalOverlay.classList.add("open");
    setTimeout(function () { DOM.modalReturns.innerHTML = renderReturns(flight.returns); }, 50);
  }

  function closeModal() {
    DOM.modalOverlay.classList.remove("open");
    currentFlight = null;
  }

  // ====== 加载数据 ======

  function loadFromObject(data) {
    flightsData.domestic = data.domestic || [];
    flightsData.international = data.international || [];
    updateMeta(data);
    renderDateFilter();
    renderFlights(getCurrentFlights());
  }

  function loadData() {
    // 先显示内置数据
    loadFromObject(INLINE_DATA);

    // 再尝试加载远程 JSON（有服务器时生效）
    DOM.refreshBtn.classList.add("spinning");
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "data/flights.json?_t=" + Date.now(), true);
    xhr.onload = function () {
      DOM.refreshBtn.classList.remove("spinning");
      if (xhr.status === 200) {
        try { loadFromObject(JSON.parse(xhr.responseText)); }
        catch (e) { /* 保持内置数据 */ }
      }
    };
    xhr.onerror = function () { DOM.refreshBtn.classList.remove("spinning"); };
    xhr.send();
  }

  // ====== 绑定事件 ======

  function init() {
    DOM.domesticCount = document.getElementById("domesticCount");
    DOM.internationalCount = document.getElementById("internationalCount");
    DOM.totalCount = document.getElementById("totalCount");
    DOM.minPrice = document.getElementById("minPrice");
    DOM.dataDate = document.getElementById("dataDate");
    DOM.updateTime = document.getElementById("updateTime");
    DOM.flightList = document.getElementById("flightList");
    DOM.summaryBar = document.getElementById("summaryBar");
    DOM.refreshBtn = document.getElementById("refreshBtn");
    DOM.tabs = document.querySelectorAll(".tab");
    DOM.dateList = document.getElementById("dateList");
    DOM.modalOverlay = document.getElementById("modalOverlay");
    DOM.modalClose = document.getElementById("modalClose");
    DOM.modalDest = document.getElementById("modalDest");
    DOM.modalSub = document.getElementById("modalSub");
    DOM.modalReturns = document.getElementById("modalReturns");

    // Tab 切换
    for (var i = 0; i < DOM.tabs.length; i++) {
      (function (t) {
        t.addEventListener("click", function () { switchTab(t.dataset.tab); });
      })(DOM.tabs[i]);
    }

    // 全部日期
    document.getElementById("dateAllBtn").addEventListener("click", function () {
      currentDate = "";
      renderDateFilter();
      renderFlights(getCurrentFlights());
    });

    // 刷新
    DOM.refreshBtn.addEventListener("click", loadData);

    // 点击卡片 → 弹窗
    DOM.flightList.addEventListener("click", function (e) {
      var card = e.target.closest(".flight-card");
      if (!card || e.target.closest("a")) return; // 忽略平台链接点击
      var idx = parseInt(card.dataset.idx, 10);
      var all = flightsData[currentTab] || [];
      var filtered = currentDate ? all.filter(function (f) { return f.date === currentDate; }) : all;
      var sorted = filtered.slice().sort(function (a, b) { return a.price - b.price; });
      if (!isNaN(idx) && sorted[idx]) openModal(sorted[idx]);
    });

    // 关闭弹窗
    DOM.modalClose.addEventListener("click", closeModal);
    DOM.modalOverlay.addEventListener("click", function (e) {
      if (e.target === DOM.modalOverlay) closeModal();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeModal();
    });

    // 启动
    loadData();
  }

  // ====== 启动 ======

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
