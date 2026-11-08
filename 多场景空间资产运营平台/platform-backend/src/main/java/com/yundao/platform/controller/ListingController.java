package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.ListingService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/guarantee")
public class ListingController {

    private final ListingService service;
    private final com.yundao.platform.service.PermissionService permissions;

    public ListingController(ListingService service,
                             com.yundao.platform.service.PermissionService permissions) {
        this.service = service;
        this.permissions = permissions;
    }

    @GetMapping("/listings")
    public R<List<Map<String, Object>>> listings(@RequestParam long projectId) {
        return R.ok(service.listings(projectId));
    }

    @PostMapping("/listings")
    public R<Map<String, Object>> create(@RequestBody ListingService.CreateCmd cmd) {
        permissions.require("listing:manage");
        return R.ok(service.create(cmd));
    }

    @PostMapping("/listings/{listingId}/publish")
    public R<Map<String, Object>> publish(@PathVariable long listingId) {
        permissions.require("listing:manage");
        return R.ok(service.publish(listingId));
    }

    @PostMapping("/listings/{listingId}/offline")
    public R<Map<String, Object>> offline(@PathVariable long listingId) {
        permissions.require("listing:manage");
        return R.ok(service.offline(listingId));
    }

    @PostMapping("/listings/{listingId}/bookings")
    public R<Map<String, Object>> book(@PathVariable long listingId,
                                       @RequestBody ListingService.BookingCmd cmd) {
        permissions.require("listing:book");
        return R.ok(service.book(listingId, cmd));
    }

    @GetMapping("/listing-orders")
    public R<List<Map<String, Object>>> orders(@RequestParam long projectId) {
        return R.ok(service.orders(projectId));
    }

    @GetMapping("/bookings")
    public R<List<Map<String, Object>>> bookings(@RequestParam long projectId) {
        return R.ok(service.bookings(projectId));
    }

    @PostMapping("/bookings/{bookingId}/confirm")
    public R<Map<String, Object>> confirm(@PathVariable long bookingId) {
        permissions.require("listing:manage");
        return R.ok(service.updateBooking(bookingId, "CONFIRMED"));
    }

    @PostMapping("/bookings/{bookingId}/cancel")
    public R<Map<String, Object>> cancel(@PathVariable long bookingId) {
        permissions.require("listing:manage");
        return R.ok(service.updateBooking(bookingId, "CANCELLED"));
    }
}
