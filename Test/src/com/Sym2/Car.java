package com.Sym2;

import java.util.HashMap;
import java.util.Map;

public class Car {

	public Car(String color, String model) {
		this.color = color;
		this.model = model;
	}
	
	String color;
	String model;
	
	@Override
	public boolean equals(Object obj) {
		if(null == obj)
			return false;
		if(!(obj instanceof Car))
			return false;
		Car c = (Car)obj;
		return c.color.equalsIgnoreCase(this.color) && this.model.equalsIgnoreCase(c.model);
	}
	
	@Override
	public int hashCode() {
		return this.color.hashCode() + this.model.hashCode();
	}
	
	public static void main(String[] args) {
		Car c = new Car("Red","A");
		Car c1 = new Car("Red","A");
		System.out.println(c.equals(c1));
		Map<Car, Car> map = new HashMap<Car, Car>();
		map.put(c, c);
		map.put(c1, c1);
		
		System.out.println(map.size());
	}

}
