package com.study;

import java.util.List;

public class list {
	public void m1(List<? extends Number> list)
	{
		Number n = list.get(0);
	}
}
