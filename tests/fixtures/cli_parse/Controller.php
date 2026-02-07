<?php
namespace app\controller;

use think\Controller;

class UserController extends Controller {
    /**
     * User login
     * @route POST /api/user/login
     */
    public function login() {
        return ['status' => 'ok'];
    }
}
