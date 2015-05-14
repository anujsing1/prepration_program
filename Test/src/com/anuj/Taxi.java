package com.anuj;

import static javax.persistence.GenerationType.IDENTITY;

import java.util.Date;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.OneToOne;
import javax.persistence.Table;

@Entity
@Table(name = "Taxi")
public class Taxi {
	private int taxiNo;
	private String regNo;
	private String model;
	private int capacity;
	private Date regDate;
	private CabDriver cabDriver;

	/**
	 * @return the taxiNo
	 */
	@Id
	@GeneratedValue(strategy = IDENTITY)
	@Column(name = "taxi_No", unique = true, nullable = false)
	public int getTaxiNo() {
		return taxiNo;
	}

	/**
	 * @param taxiNo
	 *            the taxiNo to set
	 */
	public void setTaxiNo(int taxiNo) {
		this.taxiNo = taxiNo;
	}

	/**
	 * @return the regNo
	 */
	@Column(name = "reg_No")
	public String getRegNo() {
		return regNo;
	}

	/**
	 * @param regNo
	 *            the regNo to set
	 */
	public void setRegNo(String regNo) {
		this.regNo = regNo;
	}

	/**
	 * @return the model
	 */
	@Column(name = "model")
	public String getModel() {
		return model;
	}

	/**
	 * @param model
	 *            the model to set
	 */
	public void setModel(String model) {
		this.model = model;
	}

	/**
	 * @return the capacity
	 */
	@Column(name = "capacity")
	public int getCapacity() {
		return capacity;
	}

	/**
	 * @param capacity
	 *            the capacity to set
	 */
	public void setCapacity(int capacity) {
		this.capacity = capacity;
	}

	/**
	 * @return the regDate
	 */
	@Column(name = "reg_Date")
	public Date getRegDate() {
		return regDate;
	}

	/**
	 * @param regDate
	 *            the regDate to set
	 */
	public void setRegDate(Date regDate) {
		this.regDate = regDate;
	}

	/**
	 * @return the cabDriver
	 */
	@OneToOne(mappedBy = "taxi", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
	public CabDriver getCabDriver() {
		return cabDriver;
	}

	/**
	 * @param cabDriver
	 *            the cabDriver to set
	 */
	public void setCabDriver(CabDriver cabDriver) {
		this.cabDriver = cabDriver;
	}
}
