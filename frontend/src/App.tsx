import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import RequireRole from "./components/RequireRole";
import { useAuth } from "./auth";

import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import NotFoundPage from "./pages/NotFoundPage";
import CatalogPage from "./pages/CatalogPage";
import CatalogDetailPage from "./pages/CatalogDetailPage";

import BuyerDashboardPage from "./pages/buyer/BuyerDashboardPage";
import CartPage from "./pages/buyer/CartPage";
import CheckoutPage from "./pages/buyer/CheckoutPage";
import PayPage from "./pages/buyer/PayPage";
import OrdersListPage from "./pages/buyer/OrdersListPage";
import OrderDetailPage from "./pages/buyer/OrderDetailPage";

import SellerDashboardPage from "./pages/seller/SellerDashboardPage";
import SellerProductsPage from "./pages/seller/SellerProductsPage";
import SellerProductNewPage from "./pages/seller/SellerProductNewPage";
import SellerProductEditPage from "./pages/seller/SellerProductEditPage";
import SellerOrdersPage from "./pages/seller/SellerOrdersPage";

import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AdminProductsPage from "./pages/admin/AdminProductsPage";
import AdminProductDetailPage from "./pages/admin/AdminProductDetailPage";
import AdminOrdersPage from "./pages/admin/AdminOrdersPage";

export default function App() {
  const { loading } = useAuth();
  if (loading) {
    return (
      <Layout>
        <div className="container" style={{ padding: "60px 0" }}>
          <p className="muted">Загрузка…</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/catalog/:id" element={<CatalogDetailPage />} />

        <Route element={<RequireRole roles={["buyer"]} />}>
          <Route path="/account" element={<BuyerDashboardPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/pay/:id" element={<PayPage />} />
          <Route path="/orders" element={<OrdersListPage />} />
          <Route path="/orders/:id" element={<OrderDetailPage />} />
        </Route>

        <Route element={<RequireRole roles={["seller"]} />}>
          <Route path="/seller" element={<SellerDashboardPage />} />
          <Route path="/seller/products" element={<SellerProductsPage />} />
          <Route path="/seller/products/new" element={<SellerProductNewPage />} />
          <Route path="/seller/products/:id/edit" element={<SellerProductEditPage />} />
          <Route path="/seller/orders" element={<SellerOrdersPage />} />
        </Route>

        <Route element={<RequireRole roles={["admin"]} />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/products" element={<AdminProductsPage />} />
          <Route path="/admin/products/:id" element={<AdminProductDetailPage />} />
          <Route path="/admin/orders" element={<AdminOrdersPage />} />
        </Route>

        <Route path="/index" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Layout>
  );
}
